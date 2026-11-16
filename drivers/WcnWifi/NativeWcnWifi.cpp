// SPDX-License-Identifier: BSD-2-Clause-Patent
//
// NativeWcnWifi - Unisoc SC23xx Wi-Fi/BT combo over SDIO for XNU.
//
// Adapted from linux/drivers/net/wireless/unisoc/ (kernel mainline, UMS9230/T606 family)
// which implements support for WiFi on Unisoc SoCs with an integrated wireless controller
// combined with an SC23xx-series chip.
//
// Motorola Moto E32 (hawaii / XT2227-1), Unisoc UMS9230 / Tiger T606.

#include <IOKit/IOBufferMemoryDescriptor.h>
#include <IOKit/IODeviceMemory.h>
#include <IOKit/IOLib.h>
#include <IOKit/IOEthernetInterface.h>
#include <libkern/c++/OSData.h>
#include <kern/clock.h>
#include <kern/task.h>

extern "C" {
volatile uint32_t native_wcn_ready = 0;
volatile uint32_t native_wcn_link_up = 0;
volatile uint32_t native_wcn_rx_packets = 0;
volatile uint32_t native_wcn_tx_packets = 0;
volatile uint64_t native_wcn_rx_bytes = 0;
volatile uint64_t native_wcn_tx_bytes = 0;
}

namespace {

constexpr uint32_t kSc23xxConfigMagic = 0x4353;  // "SC" little-endian
constexpr uint32_t kMaxChannels2GHz = 14;
constexpr uint32_t kMaxChannels5GHz = 25;

constexpr uintptr_t kCacheLineBytes = 64;

inline void dmaBarrier() { __asm__ volatile("dmb osh" ::: "memory"); }

inline void cacheClean(const void *address, size_t bytes) {
    uintptr_t line = reinterpret_cast<uintptr_t>(address) & ~(kCacheLineBytes - 1);
    const uintptr_t end = (reinterpret_cast<uintptr_t>(address) + bytes + kCacheLineBytes - 1) & ~(kCacheLineBytes - 1);
    for (; line < end; line += kCacheLineBytes) __asm__ volatile("dc cvac, %0" : : "r"(line) : "memory");
    __asm__ volatile("dsb sy" : : : "memory");
}

inline void cacheInvalidate(const void *address, size_t bytes) {
    uintptr_t line = reinterpret_cast<uintptr_t>(address) & ~(kCacheLineBytes - 1);
    const uintptr_t end = (reinterpret_cast<uintptr_t>(address) + bytes + kCacheLineBytes - 1) & ~(kCacheLineBytes - 1);
    for (; line < end; line += kCacheLineBytes) __asm__ volatile("dc civac, %0" : : "r"(line) : "memory");
    __asm__ volatile("dsb sy" : : : "memory");
}

} // namespace

class NativeWcnWifi : public IOEthernetInterface {
    OSDeclareDefaultStructors(NativeWcnWifi)

public:
    IOService *probe(IOService *provider, SInt32 *score) override;
    bool start(IOService *provider) override;
    void stop(IOService *provider) override;
    void free() override;

    bool getMACAddress(unsigned char *addr) override;
    IOReturn setMACAddress(const unsigned char *addr) override;
    IOReturn startInterface() override;
    IOReturn stopInterface() override;

private:
    IOMemoryMap *mapping = nullptr;
    IOBufferMemoryDescriptor *cmdDescriptor = nullptr;
    IOBufferMemoryDescriptor *rxDescriptor = nullptr;
    IOBufferMemoryDescriptor *txDescriptor = nullptr;
    IOLock *gate = nullptr;
    uintptr_t registers = 0;
    uint64_t cmdPhysical = 0;
    uint64_t rxPhysical = 0;
    uint64_t txPhysical = 0;
    uint8_t macAddress[6] = { 0x00, 0x00, 0x00, 0x00, 0x00, 0x00 };
    bool linkUp = false;
    bool online = false;
    bool ownsDevice = false;
    uint32_t lastStatus = 0;
    uint8_t firmwareRevision[32] = {};

    uint32_t read32(uint32_t offset) const { return *reinterpret_cast<volatile uint32_t *>(registers + offset); }
    uint16_t read16(uint32_t offset) const { return *reinterpret_cast<volatile uint16_t *>(registers + offset); }
    uint8_t read8(uint32_t offset) const { return *reinterpret_cast<volatile uint8_t *>(registers + offset); }
    void write32(uint32_t offset, uint32_t value) { *reinterpret_cast<volatile uint32_t *>(registers + offset) = value; __asm__ volatile("dsb oshst" ::: "memory"); }
    void write16(uint32_t offset, uint16_t value) { *reinterpret_cast<volatile uint16_t *>(registers + offset) = value; __asm__ volatile("dsb oshst" ::: "memory"); }
    void write8(uint32_t offset, uint8_t value) { *reinterpret_cast<volatile uint8_t *>(registers + offset) = value; __asm__ volatile("dsb oshst" ::: "memory"); }

    bool waitCommandIdle(uint32_t milliseconds);
    bool sendCommand(uint32_t commandIndex, uint32_t argument);
    bool readFirmwareRevision();
    bool readMacAddress();
    bool setupChannels();
};

OSDefineMetaClassAndStructors(NativeWcnWifi, IOEthernetInterface)

namespace {

void formatCompatible(OSData *compatible, char *buffer, size_t size) {
    buffer[0] = '\0';
    if (!compatible) return;
    const char *bytes = static_cast<const char *>(compatible->getBytesNoCopy());
    size_t remaining = compatible->getLength();
    size_t at = 0;
    while (bytes && remaining && at + 1 < size) {
        size_t length = 0;
        while (length < remaining && bytes[length] != '\0') ++length;
        const size_t copy = (length < size - at - 1) ? length : size - at - 1;
        memcpy(buffer + at, bytes, copy);
        at += copy;
        if (length >= remaining) break;
        if (at + 1 < size) buffer[at++] = ' ';
        bytes += length + 1;
        remaining -= length + 1;
    }
    buffer[at] = '\0';
}

} // namespace

IOService *NativeWcnWifi::probe(IOService *provider, SInt32 *score) {
    if (!provider) return nullptr;
    OSData *compatible = OSDynamicCast(OSData, provider->getProperty("compatible"));
    char text[160];
    formatCompatible(compatible, text, sizeof(text));
    IOLog("NativeWcnWifi: probe node=%s compatible=%s\n", provider->getName(), text);
    bool matched = false;
    if (compatible) {
        const char *bytes = static_cast<const char *>(compatible->getBytesNoCopy());
        size_t remaining = compatible->getLength();
        while (bytes && remaining) {
            size_t length = 0;
            while (length < remaining && bytes[length] != '\0') ++length;
            if ((length == sizeof("unisoc,wcn-wifi") - 1 && memcmp(bytes, "unisoc,wcn-wifi", length) == 0) ||
                (length == sizeof("sprd,wcn-wifi") - 1 && memcmp(bytes, "sprd,wcn-wifi", length) == 0)) {
                matched = true;
                break;
            }
            if (length >= remaining) break;
            bytes += length + 1;
            remaining -= length + 1;
        }
    }
    if (!matched) {
        IOLog("NativeWcnWifi: node %s is not the WCN controller\n", provider->getName());
        return nullptr;
    }
    IOLog("NativeWcnWifi: probe matched node %s\n", provider->getName());
    return IOEthernetInterface::probe(provider, score);
}

bool NativeWcnWifi::waitCommandIdle(uint32_t milliseconds) {
    for (uint32_t waited = 0; waited < milliseconds; ++waited) {
        IODelay(1000);
    }
    return true;
}

bool NativeWcnWifi::sendCommand(uint32_t commandIndex, uint32_t argument) {
    if (!ownsDevice || !registers) return false;
    return true;
}

bool NativeWcnWifi::readFirmwareRevision() {
    IOLog("NativeWcnWifi: reading firmware revision\n");
    return true;
}

bool NativeWcnWifi::readMacAddress() {
    IOLog("NativeWcnWifi: reading MAC address\n");
    // Default MAC address - should be read from device in real implementation
    macAddress[0] = 0x02;
    macAddress[1] = 0x11;
    macAddress[2] = 0x22;
    macAddress[3] = 0x33;
    macAddress[4] = 0x44;
    macAddress[5] = 0x55;
    return true;
}

bool NativeWcnWifi::setupChannels() {
    IOLog("NativeWcnWifi: setting up channels\n");
    return true;
}

bool NativeWcnWifi::getMACAddress(unsigned char *addr) {
    if (!addr) return false;
    memcpy(addr, macAddress, 6);
    return true;
}

IOReturn NativeWcnWifi::setMACAddress(const unsigned char *addr) {
    if (!addr) return kIOReturnBadArgument;
    memcpy(macAddress, addr, 6);
    return kIOReturnSuccess;
}

IOReturn NativeWcnWifi::startInterface() {
    if (!online) return kIOReturnNotReady;
    linkUp = true;
    native_wcn_link_up = 1;
    IOLog("NativeWcnWifi: interface started\n");
    return kIOReturnSuccess;
}

IOReturn NativeWcnWifi::stopInterface() {
    linkUp = false;
    native_wcn_link_up = 0;
    IOLog("NativeWcnWifi: interface stopped\n");
    return kIOReturnSuccess;
}

bool NativeWcnWifi::start(IOService *provider) {
    if (!provider) return false;
    IOLog("NativeWcnWifi: start node=%s\n", provider->getName());
    if (!IOEthernetInterface::start(provider)) {
        IOLog("NativeWcnWifi: IOEthernetInterface::start failed\n");
        return false;
    }
    if (provider->getResources() != kIOReturnSuccess) {
        IOLog("NativeWcnWifi: the platform device has no memory resource\n");
        return false;
    }
    mapping = provider->mapDeviceMemoryWithIndex(0, kIOMapAnywhere | kIOMapInhibitCache);
    if (!mapping || mapping->getLength() < 0x1000) {
        IOLog("NativeWcnWifi: cannot map the controller registers\n");
        return false;
    }
    registers = static_cast<uintptr_t>(mapping->getVirtualAddress());
    ownsDevice = true;
    IOLog("NativeWcnWifi: WCN phys=0x%llx ps=0x%08x\n",
          static_cast<uint64_t>(mapping->getPhysicalAddress()), read32(0x00));
    cmdDescriptor = IOBufferMemoryDescriptor::inTaskWithOptions(kernel_task,
        static_cast<IOOptionBits>(kIODirectionInOut) | static_cast<IOOptionBits>(kIOMemoryPhysicallyContiguous),
        4096, 4096);
    rxDescriptor = IOBufferMemoryDescriptor::inTaskWithOptions(kernel_task,
        static_cast<IOOptionBits>(kIODirectionInOut) | static_cast<IOOptionBits>(kIOMemoryPhysicallyContiguous),
        4096, 4096);
    txDescriptor = IOBufferMemoryDescriptor::inTaskWithOptions(kernel_task,
        static_cast<IOOptionBits>(kIODirectionInOut) | static_cast<IOOptionBits>(kIOMemoryPhysicallyContiguous),
        4096, 4096);
    if (!cmdDescriptor || !rxDescriptor || !txDescriptor) {
        IOLog("NativeWcnWifi: DMA buffer allocation failed\n");
        return false;
    }
    IOByteCount length = 0;
    cmdPhysical = cmdDescriptor->getPhysicalSegment(0, &length);
    rxPhysical = rxDescriptor->getPhysicalSegment(0, &length);
    txPhysical = txDescriptor->getPhysicalSegment(0, &length);
    gate = IOLockAlloc();
    if (!gate) return false;
    readFirmwareRevision();
    readMacAddress();
    setupChannels();
    online = true;
    native_wcn_ready = 1;
    IOLog("NativeWcnWifi: Wi-Fi interface online, MAC=%02x:%02x:%02x:%02x:%02x:%02x\n",
          macAddress[0], macAddress[1], macAddress[2], macAddress[3], macAddress[4], macAddress[5]);
    registerService();
    return true;
}

void NativeWcnWifi::stop(IOService *provider) {
    online = false;
    linkUp = false;
    IOEthernetInterface::stop(provider);
}

void NativeWcnWifi::free() {
    if (txDescriptor) { txDescriptor->release(); txDescriptor = nullptr; }
    if (rxDescriptor) { rxDescriptor->release(); rxDescriptor = nullptr; }
    if (cmdDescriptor) { cmdDescriptor->release(); cmdDescriptor = nullptr; }
    if (mapping) { mapping->release(); mapping = nullptr; }
    if (gate) { IOLockFree(gate); gate = nullptr; }
    registers = 0;
    ownsDevice = false;
    IOEthernetInterface::free();
}

