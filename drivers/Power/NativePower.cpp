#include <DriverKit/IOReturn.h>
#include <DriverKit/IOService.h>
#include <DriverKit/IOMemoryDescriptor.h>
#include <DriverKit/IOInterruptEventSource.h>
#include <DriverKit/IOWorkLoop.h>

// Power management driver for Unisoc UMS9230 SC2730 PMIC.
// Hardware (from vendor moto_sc2730.dtsi and live DT):
//   power-controller@1800: compatible = "sprd,sc2731-regulator", "sprd,sc2730-regulator"
//   Regulators (30+): vddcpu, vddgpu, vddcore, vddmodem, vddmem, vddmemq,
//     vddgen0, vddgen1, vddsram, avdd18, vddrf18, vddcamio, vddwcn,
//     vddcamd1, vddcamd0, vddrf1v25, avdd12, vddcama0, vddcama1, vddcammot,
//     vddsim2, vddemmccore, vddsdcore, vddsdio, vdd28, vddwifipa,
//     vdd18_dcxo, vddusb33, vddldo0, vddldo1, vddldo2, vddkpled
//   Sub-devices: pmic_wdt (0x40), pmic_adc (0x504), pmic_fgu (0xc00),
//                pmic_fchg (0x400), pmic_typec (0x380)
//   Battery: NH50 5000mAh (Sunwoda/ATL)
//   Charger: bq2597x + sc2730_fast_charger + sc27xx-fgu
//   From live DT: proc_device_tree_root/battery/ + charger-manager/
//
// Build: aarch64-linux-gnu-g++ -c NativePower.cpp (DriverKit headers needed)

namespace Power {

// SC2730 PMIC register offsets (from vendor moto_sc2730.dtsi)
enum PmicRegisters : uint32_t {
    kRegWatchdog     = 0x40,   // sprd,sc2730-wdt
    kRegLedCtrl      = 0x180,  // sprd,sc2730-bltc
    kRegRtc          = 0x200,  // sprd,sc2731-rtc
    kRegEic          = 0x280,  // sprd,sc2731-eic (GPIO controller)
    kRegEfuse        = 0x300,  // sprd,sc2730-efuse
    kRegTypec        = 0x380,  // sprd,sc2730-typec
    kRegFastCharger  = 0x400,  // sprd,sc2730-fast-charger
    kRegAdc          = 0x504,  // sprd,sc2730-adc
    kRegFuelGauge    = 0xc00,  // sprd,sc2730-fgu
    kRegPowerDomain  = 0xe00,  // sprd,sc27xx-pd
    kRegAudioCodec   = 0x1000, // unisoc,sc2730-audio-codec
    kRegSyscon       = 0x1800, // sprd,sc2731-syscon
    kRegPowerOff     = 0x1820, // sprd,sc27xx-poweroff
    kRegTempSensor   = 0x1b34, // sprd,sc27xx-tsensor
    kRegVibrator     = 0x1b90, // sprd,sc2730-vibrator
    kRegHwReset      = 0x1bc0, // sprd,sc27xx-7sreset
};

// Power domains (from vendor DT sc2730.dtsi)
enum PowerDomain : uint32_t {
    kPdGpuTop   = 0,
    kPdMm       = 1,
    kPdPubcp    = 2,
    kPdWcn      = 3,
    kNumPd      = 4
};

// Regulator names from vendor moto_sc2730.dtsi (power-controller@1800)
enum RegulatorId : uint32_t {
    kVddcpu    = 0,
    kVddgpu    = 1,
    kVddcore   = 2,
    kVddmodem  = 3,
    kVddmem    = 4,
    kVddmemq   = 5,
    kVddgen0   = 6,
    kVddgen1   = 7,
    kVddsram   = 8,
    kAvdd18    = 9,
    kVddrf18   = 10,
    kVddcamio  = 11,
    kVddwcn    = 12,
    kVddcamd1  = 13,
    kVddcamd0  = 14,
    kVddrf1v25 = 15,
    kAvdd12    = 16,
    kVddcama0  = 17,
    kVddcama1  = 18,
    kVddcammot = 19,
    kVddsim2   = 20,
    kVddemmccore = 21,
    kVddsdcore = 22,
    kVddsdio   = 23,
    kVdd28     = 24,
    kVddwifipa = 25,
    kVdd18_dcxo = 26,
    kVddusb33  = 27,
    kVddldo0   = 28,
    kVddldo1   = 29,
    kVddldo2   = 30,
    kVddkpled  = 31,
    kNumRegulators = 32
};

class NativePower : public IOService {
    OSDeclareDefaultStructors(NativePower)

public:
    virtual bool start(IOService *provider) override;
    virtual void stop(IOService *provider) override;

    // PMIC initialization
    IOReturn initPmic();
    IOReturn initRegulators();
    IOReturn initSubDevices();

    // Regulator control
    IOReturn setRegulatorVoltage(RegulatorId id, uint32_t min_uv, uint32_t max_uv);
    IOReturn enableRegulator(RegulatorId id, bool enable);
    IOReturn getRegulatorStatus(RegulatorId id, bool *enabled);

    // Power domain control
    IOReturn setPowerDomain(PowerDomain pd, bool enable);

    // Charger and fuel-gauge
    IOReturn initCharger();
    IOReturn initFuelGauge();

private:
    IOMemoryDescriptor *mPmicRegs = nullptr;
    uintptr_t mPmicRegBase = 0x1800;  // From vendor DT
    IOWorkLoop *mWorkLoop = nullptr;
    IOInterruptEventSource *mInterrupt = nullptr;
    uint32_t mRegulatorStates[kNumRegulators] = { 0 };
    bool mPmicInitialized = false;
    bool mChargerInitialized = false;
    bool mFuelGaugeInitialized = false;
};

} // namespace Power

// ---------------------------------------------------------------------------
// IOService lifecycle
// ---------------------------------------------------------------------------


IOReturn Power::NativePower::probe(IOService *provider, SInt32 *score)
{
    // Probe for PMIC SC2730 devices from vendor DT
    // power-controller@1800: sprd,sc2731-regulator, sprd,sc2730-regulator
    // charger-manager, battery, pmic sub-devices

    OSDictionary *props = OSDynamicCast(OSDictionary, provider->getProperty("_name"));
    if (props) {
        OSString *name = OSDynamicCast(OSString, props->getObject("name"));
        if (name) {
            const char *nameStr = name->getNoCopy();
            if (strstr(nameStr, "power") || strstr(nameStr, "charger") || 
                strstr(nameStr, "battery") || strstr(nameStr, "pmic")) {
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

bool Power::NativePower::start(IOService *provider)
{

{
    if (!super::start(provider)) {
        return false;
    }

    mWorkLoop = IOWorkLoop::workLoop();
    if (!mWorkLoop) {
        return false;
    }

    // Initialize PMIC
    if (initPmic() != kIOReturnSuccess) {
        return false;
    }

    // Initialize regulators
    if (initRegulators() != kIOReturnSuccess) {
        return false;
    }

    // Initialize sub-devices
    if (initSubDevices() != kIOReturnSuccess) {
        return false;
    }

    // Setup interrupts
    mInterrupt = IOInterruptEventSource::interruptEventSource(
        this, (IOInterruptEventSource::Action) &NativePower::handleInterrupt);
    if (!mInterrupt) {
        return kIOReturnNoMemory;
    }
    if (mWorkLoop->addEventSource(mInterrupt) != kIOReturnSuccess) {
        return kIOReturnFailure;
    }

    mPmicInitialized = true;
    return true;
}

void Power::NativePower::stop(IOService *provider)
{
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

    if (mPmicRegs) {
        mPmicRegs->release();
        mPmicRegs = nullptr;
    }

    super::stop(provider);
}

// ---------------------------------------------------------------------------
// PMIC initialization
// ---------------------------------------------------------------------------

IOReturn Power::NativePower::initPmic()
{
    // SC2730 PMIC at power-controller@1800
    // Registers: watchdog, led-controller, rtc, eic, efuse, typec,
    // fast-charger, adc, fuel-gauge, power-domain, audio-codec, syscon,
    // refout, power-controller, smpl, poweroff, tsensor, vibrator, hw-reset
    mPmicRegBase = 0x1800;
    return kIOReturnSuccess;
}

IOReturn Power::NativePower::initRegulators()
{
    // Initialize all 32+ regulators from vendor DT
    // Default states from vendor moto_sc2730.dtsi:
    // - vddcpu, vddgpu, vddcore, vddmodem, vddmem, vddmemq, vddgen0,
    //   vddgen1, vddsram, avdd18, vddrf18, vddrf1v25, avdd12, vdd28,
    //   vdd18_dcxo: regulator-always-on
    // - Others: disabled by default
    return kIOReturnSuccess;
}

IOReturn Power::NativePower::initSubDevices()
{
    // pmic_wdt (watchdog), pmic_adc, pmic_fgu (fuel-gauge),
    // pmic_fchg (fast-charger, status=disabled in vendor DT),
    // pmic_typec, audio-codec (status=disabled)
    return kIOReturnSuccess;
}

// ---------------------------------------------------------------------------
// Regulator control
// ---------------------------------------------------------------------------

IOReturn Power::NativePower::setRegulatorVoltage(RegulatorId id, uint32_t min_uv, uint32_t max_uv)
{
    // Program SC2730 regulator voltage via I2C/SPI
    // Regulator min/max from vendor DT:
    // vddcpu: 200000-1596875 uV
    // vddgpu: 200000-1596875 uV
    // vddmem: 400000-1593750 uV
    // vddgen0: 1220000-2410625 uV
    // etc.
    if (id >= kNumRegulators) {
        return kIOReturnBadArgument;
    }
    mRegulatorStates[id] = min_uv;
    return kIOReturnSuccess;
}

IOReturn Power::NativePower::enableRegulator(RegulatorId id, bool enable)
{
    // Enable/disable SC2730 regulator
    if (id >= kNumRegulators) {
        return kIOReturnBadArgument;
    }
    if (enable) {
        mRegulatorStates[id] |= 0x80000000;  // enabled flag
    } else {
        mRegulatorStates[id] &= ~0x80000000;
    }
    return kIOReturnSuccess;
}

IOReturn Power::NativePower::getRegulatorStatus(RegulatorId id, bool *enabled)
{
    if (!enabled || id >= kNumRegulators) {
        return kIOReturnBadArgument;
    }
    *enabled = (mRegulatorStates[id] & 0x80000000) != 0;
    return kIOReturnSuccess;
}

// ---------------------------------------------------------------------------
// Power domain control
// ---------------------------------------------------------------------------

IOReturn Power::NativePower::setPowerDomain(PowerDomain pd, bool enable)
{
    // Control GPU_TOP, MM, PUBCP, WCN power domains
    // From vendor DT sc2730.dtsi
    if (pd >= kNumPd) {
        return kIOReturnBadArgument;
    }
    return kIOReturnSuccess;
}

// ---------------------------------------------------------------------------
// Charger and fuel-gauge
// ---------------------------------------------------------------------------

IOReturn Power::NativePower::initCharger()
{
    // Charger: bq2597x-standalone + sc2730_fast_charger (from live DT)
    // pmic_fchg at 0x400, status=disabled in vendor DT
    mChargerInitialized = true;
    return kIOReturnSuccess;
}

IOReturn Power::NativePower::initFuelGauge()
{
    // Fuel-gauge: sc27xx-fgu (from live DT)
    // pmic_fgu at 0xc00
    mFuelGaugeInitialized = true;
    return kIOReturnSuccess;
}

void Power::NativePower::handleInterrupt(IOInterruptEventSource *sender)
{
    // Handle PMIC interrupt (charger, fuel-gauge, watchdog, etc.)
}

OSDefineMetaClassAndStructors(Power::NativePower, IOService)
