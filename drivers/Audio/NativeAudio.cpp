#include <DriverKit/IOReturn.h>
#include <DriverKit/IOService.h>
#include <DriverKit/IOMemoryDescriptor.h>
#include <DriverKit/IOInterruptEventSource.h>
#include <DriverKit/IOWorkLoop.h>

// Audio driver for Unisoc UMS9230 audio subsystem.
// Hardware (from live DT proc_device_tree_root/):
//   sound@0: compatible = "sprd,vbc-v4-codec-sc2730" (voice codec)
//   sound@1: compatible = "sprd,i2s-null-codec" (I2S null codec)
//   audio-dsp-dump@0: compatible = "sprd,audio-dsp-log" (mailbox, rxblocksize=0x2000)
//   audio-sipc: compatible = "sprd,audio_sipc" (mailbox-core=5)
//   sprd_audio_codec_ana: compatible = "unisoc,sc2730-audio-codec" (reg=0x1000)
//   From vendor moto_sc2730.dtsi: sprd,sc2730-regulator, audio-codec@1000
//
// DSP firmware and ABI not extracted — no UniXNU audio driver for
// Unisoc audio DSP exists yet. This is a skeleton driver.
//
// Build: aarch64-linux-gnu-g++ -c NativeAudio.cpp (DriverKit headers needed)

namespace Audio {

// Audio component indices (from vendor DT)
enum AudioComponent : uint32_t {
    kVoiceCodec   = 0,   // sprd,vbc-v4-codec-sc2730
    kI2sNull      = 1,   // sprd,i2s-null-codec
    kDspLog       = 2,   // sprd,audio-dsp-log
    kSipc         = 3,   // sprd,audio_sipc
    kNumComponents = 4
};

// Audio register offsets (SC2730 audio codec @ 0x1000)
enum AudioRegisters : uint32_t {
    kCodecControl   = 0x000,
    kCodecStatus    = 0x004,
    kCodecConfig    = 0x008,
    kDmaControl     = 0x100,
    kDmaStatus      = 0x104,
    kIrqStatus      = 0x200,
    kIrqMask        = 0x204,
};

// SC2730 PMIC audio-related regulators (from vendor moto_sc2730.dtsi)
enum AudioRegulator : uint32_t {
    kVddldo1  = 0,   // LDO_VDDLDO1 - audio power
    kAvdd18   = 1,   // LDO_AVDD18
    kAvdd12   = 2,   // LDO_AVDD12
    kNumAudioRegulators = 3
};

class NativeAudio : public IOService {
    OSDeclareDefaultStructors(NativeAudio)

public:
    virtual bool start(IOService *provider) override;
    virtual void stop(IOService *provider) override;

    // Audio subsystem initialization
    IOReturn initCodec();
    IOReturn initDsp();
    IOReturn initSipc();
    IOReturn setupInterrupts();
    IOReturn configureClocks();

    // Audio routing
    IOReturn routeAudioPath(uint32_t path);
    IOReturn setSampleRate(uint32_t rate_hz);
    IOReturn setAudioPower(bool enable);

private:
    IOMemoryDescriptor *mCodecRegs = nullptr;
    uintptr_t mCodecRegBase = 0x1000;  // From vendor DT
    IOWorkLoop *mWorkLoop = nullptr;
    IOInterruptEventSource *mInterrupt = nullptr;
    uint32_t mAudioComponents = 0;
    bool mCodecInitialized = false;
    bool mDspInitialized = false;
};

} // namespace Audio

// ---------------------------------------------------------------------------
// IOService lifecycle
// ---------------------------------------------------------------------------


IOReturn Audio::NativeAudio::probe(IOService *provider, SInt32 *score)
{
    // Probe for audio codec devices from vendor DT
    // sound@0: sprd,vbc-v4-codec-sc2730
    // sound@1: sprd,i2s-null-codec
    // audio-dsp-dump@0: sprd,audio-dsp-log
    // audio-sipc: sprd,audio_sipc
    // sprd_audio_codec_ana: unisoc,sc2730-audio-codec

    // Check if provider matches our audio components
    OSDictionary *props = OSDynamicCast(OSDictionary, provider->getProperty("_name"));
    if (props) {
        OSString *name = OSDynamicCast(OSString, props->getObject("name"));
        if (name) {
            const char *nameStr = name->getNoCopy();
            if (strstr(nameStr, "sound") || strstr(nameStr, "audio") || strstr(nameStr, "codec")) {
                *score = 100;
                return kIOReturnSuccess;
            }
        }
    }
    return kIOReturnFailure;
}

// ---------------------------------------------------------------------------
// IOService lifecycle
// ---------------------------------------------------------------------------

bool Audio::NativeAudio::start(IOService *provider)
{

{
    if (!super::start(provider)) {
        return false;
    }

    mWorkLoop = IOWorkLoop::workLoop();
    if (!mWorkLoop) {
        return false;
    }

    // Initialize audio codec (sprd,vbc-v4-codec-sc2730)
    if (initCodec() != kIOReturnSuccess) {
        return false;
    }

    // Initialize DSP (sprd,audio-dsp-log)
    if (initDsp() != kIOReturnSuccess) {
        return false;
    }

    // Initialize SIP communication (sprd,audio_sipc)
    if (initSipc() != kIOReturnSuccess) {
        return false;
    }

    // Setup interrupts
    if (setupInterrupts() != kIOReturnSuccess) {
        return false;
    }

    // Configure clocks from SC2730 PMIC
    if (configureClocks() != kIOReturnSuccess) {
        return false;
    }

    mAudioComponents |= (1 << kVoiceCodec) | (1 << kI2sNull) |
                        (1 << kDspLog) | (1 << kSipc);
    return true;
}

void Audio::NativeAudio::stop(IOService *provider)
{
    setAudioPower(false);

    if (mInterrupt) {
        mInterrupt->disable();
        mInterrupt->detach();
        mInterrupt->release();
        mInterrupt = nullptr;
    }

    if (mWorkLoop) {
        mWorkLoop->release();
        mWorkLoop = nullptr;
    }

    if (mCodecRegs) {
        mCodecRegs->release();
        mCodecRegs = nullptr;
    }

    super::stop(provider);
}

// ---------------------------------------------------------------------------
// Audio subsystem initialization
// ---------------------------------------------------------------------------

IOReturn Audio::NativeAudio::initCodec()
{
    // sprd,vbc-v4-codec-sc2730 - voice codec
    // sprd,i2s-null-codec - I2S null codec
    // unisoc,sc2730-audio-codec - analog codec (reg=0x1000, status=disabled in vendor DT)

    mCodecRegBase = 0x1000;  // From vendor moto_sc2730.dtsi
    mCodecInitialized = true;
    return kIOReturnSuccess;
}

IOReturn Audio::NativeAudio::initDsp()
{
    // sprd,audio-dsp-log - DSP log mailbox
    // rxblocksize = 0x2000 from live DT
    mDspInitialized = true;
    return kIOReturnSuccess;
}

IOReturn Audio::NativeAudio::initSipc()
{
    // sprd,audio_sipc - mailbox-core=5 from live DT
    return kIOReturnSuccess;
}

IOReturn Audio::NativeAudio::setupInterrupts()
{
    // Audio interrupts from SC2730 PMIC
    // In DriverKit, interrupt vector comes from DT node
    mInterrupt = IOInterruptEventSource::interruptEventSource(
        this, (IOInterruptEventSource::Action) &NativeAudio::handleInterrupt);
    if (!mInterrupt) {
        return kIOReturnNoMemory;
    }
    if (mWorkLoop->addEventSource(mInterrupt) != kIOReturnSuccess) {
        return kIOReturnFailure;
    }
    return kIOReturnSuccess;
}

IOReturn Audio::NativeAudio::configureClocks()
{
    // Audio clocks managed via SC2730 PMIC (ap_apb_regs syscon @ 0x20000000)
    // Regulators: vddldo1, avdd18, avdd12
    return kIOReturnSuccess;
}

// ---------------------------------------------------------------------------
// Audio routing and control
// ---------------------------------------------------------------------------

IOReturn Audio::NativeAudio::routeAudioPath(uint32_t path)
{
    // Route audio between codec, DSP, and output
    return kIOReturnSuccess;
}

IOReturn Audio::NativeAudio::setSampleRate(uint32_t rate_hz)
{
    // Set audio sample rate via codec registers
    return kIOReturnSuccess;
}

IOReturn Audio::NativeAudio::setAudioPower(bool enable)
{
    // Enable/disable audio power via SC2730 PMIC regulators
    return kIOReturnSuccess;
}

void Audio::NativeAudio::handleInterrupt(IOInterruptEventSource *sender)
{
    // Handle audio interrupt
    // Acknowledge and dispatch to appropriate subsystem
}

OSDefineMetaClassAndStructors(Audio::NativeAudio, IOService)
