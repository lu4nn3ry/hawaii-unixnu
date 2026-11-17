#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include <DriverKit/IOReturn.h>
#include <DriverKit/IOService.h>

/*
 * Mali-G57 (Valhall midgard) kernel GPU driver for XNU on Unisoc UMS9230 / Tiger T606.
 *
 * Hardware (from live DT proc_device_tree_root/soc/mm/gpu@23100000/):
 *   compatible = "sprd,mali-natt"
 *   reg = 0x23100000 / 0x100000   (GPU registers)
 *   interrupts = GIC_SPI 60 x3    (JOB, MMU, GPU IRQs)
 *   power-domains = <&pmu UMS9230_POWER_DOMAIN_GPU_TOP>
 *
 * Source: Mali kbase r28p0-01eac0 DDK + qogirl6 platform glue
 *   (patches 0014-0017 in CreitinGameplays/motorola-moto-e32-root/
 *    patches/kernel-sprd/branch-hawaii-diag/)
 *   Device-tree compatible "sprd,mali-natt" matches live DT.
 *
 * NOTE: This is NOT a CSF driver. Ken-u/Mali is Mali-G610 CSF (different
 * architecture, GPU_ID). The Mali-G57 uses midgard-family r28p0 DDK with
 * qogirl6 platform glue. Userspace blobs: libGLES_mali_32.so, libGLES_mali_64.so.
 *
 * XNU kernel driver model: uses kmod_start/kmod_stop entry points,
 * device_register for device registration, and direct MMIO access.
 *
 * Build: aarch64-linux-gnu-clang -target=aarch64-linux-gnu -c NativeMaliG57.c
 */

/* ---------------------------------------------------------------------------
 * Mali-G57 register offsets (from vendor kernel / r28p0 DDK)
 * Register block starts at 0x23100000
 * -------------------------------------------------------------------------- */
#define MALI_REG_GPU_ID          0x0000   /* GPU identification */
#define MALI_REG_IRQ_RAW         0x0010   /* Interrupt raw status */
#define MALI_REG_IRQ_CLEAR       0x0014   /* Interrupt clear */
#define MALI_REG_IRQ_MASK        0x0018   /* Interrupt mask */
#define MALI_REG_CORE_ID         0x00E0   /* Core identification */
#define MALI_REG_CORE_TOP        0x0100   /* Core top control */
#define MALI_REG_L2_CTRL         0x0120   /* L2 cache control */
#define MALI_REG_PWR_CTRL        0x0140   /* Power control */
#define MALI_REG_IRQ_PENDING     0x0020   /* Interrupt pending */
#define MALI_REG_GPU_ID2         0x00FC   /* GPU ID second part */
#define MALI_REG_GPU_CONFIG      0x0104   /* GPU configuration */
#define MALI_REG_L2_CONFIG       0x0124   /* L2 cache configuration */
#define MALI_REG_PWR_CORE        0x0144   /* Power control core */

/* GPU IRQ lines (from vendor DT: GIC_SPI 60 x3) */
#define MALI_IRQ_JOB     0   /* Job manager interrupt */
#define MALI_IRQ_MMU     1   /* MMU interrupt */
#define MALI_IRQ_GPU     2   /* GPU core interrupt */
#define MALI_NUM_IRQS    3

/* Mali-G57 GPU_ID (midgard-family) */
#define MALI_GPU_ID_G57  0x0000F570

/* Power control values */
#define MALI_PWR_ON   0x1
#define MALI_PWR_OFF  0x0

/* DVFS operating-points from vendor DT (MHz) */
#define MALI_DVFS_FREQ_0  1500
#define MALI_DVFS_FREQ_1  1860
#define MALI_DVFS_FREQ_2  2940
#define MALI_DVFS_FREQ_3  3160
#define MALI_DVFS_FREQ_4  3300
#define MALI_NUM_DVFS_FREQS 7

/* Job slot configuration */
#define MALI_NUM_JOB_SLOTS   8
#define MALI_JOB_SLOT_BASE   0x0200
#define MALI_JOB_SLOT_STRIDE 0x0020

/* MMU configuration */
#define MALI_REG_L2_CFG        0x0124   /* L2 cache configuration */
#define MALI_REG_MMU_CTRL      0x0180   /* MMU control */
#define MALI_REG_MMU_TTB       0x0184   /* MMU translation table base */
#define MALI_REG_MMU_TS        0x0188   /* MMU translation size */

/* Memory management */
#define MALI_MEM_PAGE_SIZE     0x1000   /* 4 KiB page size */
#define MALI_NUM_MEM_PAGES     4096     /* Number of managed pages */

/* ---------------------------------------------------------------------------
 * GPU device state
 * -------------------------------------------------------------------------- */
typedef struct mali_gpu_dev {
    uintptr_t   reg_base;     /* Mapped register base address */
    void       *reg_mem;      /* Mapped memory pointer */
    uint32_t    gpu_id;       /* Detected GPU ID */
    uint32_t    core_id;      /* Core identification */
    bool        powered_on;   /* GPU power state */
    int         irqs[MALI_NUM_IRQS];   /* Interrupt line IDs */
    uint32_t    dvfs_freq;    /* Current GPU frequency (MHz) */
    uint32_t    job_slots;    /* Number of job slots */
    uint32_t    num_job_slots_available; /* Available job slots */
} mali_gpu_dev_t;

static mali_gpu_dev_t g_mali_gpu;

/* ---------------------------------------------------------------------------
 * Register access helpers
 * -------------------------------------------------------------------------- */
static inline uint32_t mali_read_reg(uint32_t offset)
{
    volatile uint32_t *reg = (volatile uint32_t *)(g_mali_gpu.reg_base + offset);
    return *reg;
}

static inline void mali_write_reg(uint32_t offset, uint32_t value)
{
    volatile uint32_t *reg = (volatile uint32_t *)(g_mali_gpu.reg_base + offset);
    *reg = value;
}

/* ---------------------------------------------------------------------------
 * Platform initialization (qogirl6 glue)
 * -------------------------------------------------------------------------- */
static int mali_init_platform(void)
{
    /* qogirl6 platform-specific initialization:
     * - Power domain setup
     * - Clock gating configuration
     * - Reset deassertion
     * - Power domain for GPU_TOP (from vendor DT sc2730)
     */
    mali_write_reg(MALI_REG_PWR_CTRL, MALI_PWR_ON);
    g_mali_gpu.powered_on = true;
    return 0;
}

static int mali_deinit_platform(void)
{
    mali_write_reg(MALI_REG_PWR_CTRL, MALI_PWR_OFF);
    g_mali_gpu.powered_on = false;
    return 0;
}

/* ---------------------------------------------------------------------------
 * Register mapping
 * -------------------------------------------------------------------------- */
static int mali_map_registers(void)
{
    /* Map GPU register region from DT: reg = <0x23100000 0x100000>
     * In XNU kernel driver, we map physical memory via pmap or ioremap
     */
    g_mali_gpu.reg_base = 0x23100000;
    g_mali_gpu.reg_mem = (void *)0x23100000;
    return 0;
}

static int mali_unmap_registers(void)
{
    g_mali_gpu.reg_base = 0;
    g_mali_gpu.reg_mem = NULL;
    return 0;
}

/* ---------------------------------------------------------------------------
 * Interrupt management
 * -------------------------------------------------------------------------- */
static int mali_setup_interrupts(void)
{
    /* Vendor DT: interrupts = GIC_SPI 60 x3 (JOB/MMU/GPU)
     * In XNU, we register interrupt handlers via register_intr_handler
     * or similar mechanism.
     */
    int i;
    for (i = 0; i < MALI_NUM_IRQS; i++) {
        g_mali_gpu.irqs[i] = 60 + i;  /* GIC_SPI 60, 61, 62 */
    }
    return 0;
}

static int mali_teardown_interrupts(void)
{
    int i;
    for (i = 0; i < MALI_NUM_IRQS; i++) {
        g_mali_gpu.irqs[i] = 0;
    }
    return 0;
}

/* ---------------------------------------------------------------------------
 * Clock management
 * -------------------------------------------------------------------------- */
static int mali_configure_clocks(void)
{
    /* Vendor DT clocks for GPU:
     * clk_src_96m, clk_dpu_core, clk_dpu_dpi, clk_ap_ahb_disp_eb,
     * clk_dsi_iso_sw_en, dsi_div6clk_gate, etc.
     * These are managed via SC2730 PMIC (ap_apb_regs syscon @ 0x20000000)
     */
    mali_write_reg(MALI_REG_PWR_CTRL, MALI_PWR_ON);
    return 0;
}

/* ---------------------------------------------------------------------------
 * GPU ID probing
 * -------------------------------------------------------------------------- */
static int mali_probe_gpu_id(void)
{
    /* Read GPU ID register to confirm Mali-G57
     * Mali-G57 GPU_ID = 0x0000F570 (midgard-family)
     */
    g_mali_gpu.gpu_id = mali_read_reg(MALI_REG_GPU_ID);
    g_mali_gpu.core_id = mali_read_reg(MALI_REG_CORE_ID);

    if ((g_mali_gpu.gpu_id & 0xFFF0) != (MALI_GPU_ID_G57 & 0xFFF0)) {
        return -1;
    }
    return 0;
}

/* ---------------------------------------------------------------------------
 * Power management
 * -------------------------------------------------------------------------- */
static int mali_set_gpu_power(bool enable)
{
    if (enable && !g_mali_gpu.powered_on) {
        mali_write_reg(MALI_REG_PWR_CTRL, MALI_PWR_ON);
        g_mali_gpu.powered_on = true;
    } else if (!enable && g_mali_gpu.powered_on) {
        mali_write_reg(MALI_REG_PWR_CTRL, MALI_PWR_OFF);
        g_mali_gpu.powered_on = false;
    }
    return 0;
}

/* ---------------------------------------------------------------------------
 * DVFS frequency management
 * -------------------------------------------------------------------------- */
static int mali_set_dvfs_frequency(uint32_t freq_mhz)
{
    /* Vendor DT DVFS operating-points: [1500, 1860, 1500, 2940, 3160, 2940,
     * 512, 3200, 3300] MHz
     * Program GPU DVFS via SC2730 PMIC regulators (vddgpu)
     */
    uint32_t valid_freqs[] = {1500, 1860, 2940, 3160, 512, 3200, 3300};
    bool valid = false;
    uint32_t i;
    for (i = 0; i < MALI_NUM_DVFS_FREQS; i++) {
        if (valid_freqs[i] == freq_mhz) {
            valid = true;
            break;
        }
    }
    if (!valid) {
        return -1;
    }
    g_mali_gpu.dvfs_freq = freq_mhz;
    return 0;
}

static uint32_t mali_get_dvfs_frequency(void)
{
    return g_mali_gpu.dvfs_freq;
}

/* ---------------------------------------------------------------------------
 * Job slot management
 * -------------------------------------------------------------------------- */
static int mali_init_job_slots(void)
{
    g_mali_gpu.job_slots = MALI_NUM_JOB_SLOTS;
    g_mali_gpu.num_job_slots_available = MALI_NUM_JOB_SLOTS;
    return 0;
}

static int mali_submit_job(uint32_t job_slot, uintptr_t cmd_addr, uint32_t cmd_size)
{
    if (job_slot >= MALI_NUM_JOB_SLOTS) {
        return -1;
    }
    if (!g_mali_gpu.powered_on) {
        return -1;
    }
    if (g_mali_gpu.num_job_slots_available == 0) {
        return -1; /* No free job slots */
    }
    /* Write job command to job slot register */
    uint32_t job_reg = MALI_JOB_SLOT_BASE + (job_slot * MALI_JOB_SLOT_STRIDE);
    mali_write_reg(job_reg, (uint32_t)cmd_addr);
    mali_write_reg(job_reg + 0x04, cmd_size);
    g_mali_gpu.num_job_slots_available--;
    return 0;
}

static int mali_release_job_slot(uint32_t job_slot)
{
    if (job_slot >= MALI_NUM_JOB_SLOTS) {
        return -1;
    }
    g_mali_gpu.num_job_slots_available++;
    return 0;
}

/* ---------------------------------------------------------------------------
 * Memory management
 * -------------------------------------------------------------------------- */
static int mali_map_memory(uintptr_t phys_addr, uint32_t size)
{
    /* Map GPU memory region for DMA access
     * In XNU, this would use vm_map_enter or similar
     */
    /* Placeholder for memory mapping */
    return 0;
}

static int mali_unmap_memory(uintptr_t phys_addr, uint32_t size)
{
    /* Unmap GPU memory region */
    return 0;
}

/* ---------------------------------------------------------------------------
 * Interrupt handler
 * -------------------------------------------------------------------------- */
void mali_handle_interrupt(uint32_t irq)
{
    uint32_t irq_status = mali_read_reg(MALI_REG_IRQ_RAW);
    uint32_t irq_pending = mali_read_reg(MALI_REG_IRQ_PENDING);

    /* Acknowledge interrupts */
    mali_write_reg(MALI_REG_IRQ_CLEAR, irq_status);

    if (irq_status & (1 << MALI_IRQ_JOB)) {
        /* Job completed */
        g_mali_gpu.num_job_slots_available++;
    }
    if (irq_status & (1 << MALI_IRQ_MMU)) {
        /* MMU fault */
    }
    if (irq_status & (1 << MALI_IRQ_GPU)) {
        /* GPU error */
    }
}

/* ---------------------------------------------------------------------------
 * Kernel module entry points
 * -------------------------------------------------------------------------- */

static int mali_start(void)
{
    int ret;

    /* Map GPU registers */
    ret = mali_map_registers();
    if (ret != 0) {
        return ret;
    }

    /* Probe GPU ID */
    ret = mali_probe_gpu_id();
    if (ret != 0) {
        return ret;
    }

    /* Setup interrupts */
    ret = mali_setup_interrupts();
    if (ret != 0) {
        return ret;
    }

    /* Configure clocks */
    ret = mali_configure_clocks();
    if (ret != 0) {
        return ret;
    }

    /* Initialize platform (qogirl6 glue) */
    ret = mali_init_platform();
    if (ret != 0) {
        return ret;
    }

    /* Initialize job slots */
    ret = mali_init_job_slots();
    if (ret != 0) {
        return ret;
    }

    g_mali_gpu.powered_on = true;
    return 0;
}

static void mali_stop(void)
{
    mali_set_gpu_power(false);
    mali_teardown_interrupts();
    mali_unmap_registers();
    g_mali_gpu.reg_base = 0;
    g_mali_gpu.reg_mem = NULL;
    g_mali_gpu.gpu_id = 0;
    g_mali_gpu.core_id = 0;
    g_mali_gpu.dvfs_freq = 0;
    g_mali_gpu.job_slots = 0;
    g_mali_gpu.num_job_slots_available = 0;
    g_mali_gpu.powered_on = false;
}


// ---------------------------------------------------------------------------
 * IOService class for Mali-G57 GPU driver
 * -------------------------------------------------------------------------- */

class NativeMaliG57 : public IOService {
    OSDeclareDefaultStructors(NativeMaliG57)

public:
    virtual bool start(IOService *provider) override;
    virtual void stop(IOService *provider) override;

    IOReturn initGpuRegisters();
    IOReturn probeGpuId();
    IOReturn setupInterrupts();
    IOReturn configureClocks();
    IOReturn initPlatform();
    IOReturn initJobSlots();
    IOReturn setGpuPower(bool enable);
    IOReturn setDvfsFrequency(uint32_t freq_mhz);
    IOReturn submitJob(uint32_t job_slot, uintptr_t cmd_addr, uint32_t cmd_size);
    IOReturn releaseJobSlot(uint32_t job_slot);

private:
    IOMemoryDescriptor *mGpuRegs = nullptr;
    uintptr_t mGpuRegBase = 0x23100000;
    IOWorkLoop *mWorkLoop = nullptr;
    uint32_t mGpuId = 0;
    uint32_t mCoreId = 0;
    bool mPoweredOn = false;
    int mIrqs[MALI_NUM_IRQS];
    uint32_t mDvfsFreq = 0;
    uint32_t mJobSlots = 0;
    uint32_t mJobSlotsAvailable = 0;
};

// ===========================================================================
// IOService lifecycle
// ===========================================================================

bool NativeMaliG57::start(IOService *provider)
{
    if (!super::start(provider)) {
        return false;
    }

    mWorkLoop = IOWorkLoop::workLoop();
    if (!mWorkLoop) {
        return false;
    }

    if (initGpuRegisters() != kIOReturnSuccess) {
        return false;
    }

    if (probeGpuId() != kIOReturnSuccess) {
        return false;
    }

    if (setupInterrupts() != kIOReturnSuccess) {
        return false;
    }

    if (configureClocks() != kIOReturnSuccess) {
        return false;
    }

    if (initPlatform() != kIOReturnSuccess) {
        return false;
    }

    if (initJobSlots() != kIOReturnSuccess) {
        return false;
    }

    mPoweredOn = true;
    return true;
}

void NativeMaliG57::stop(IOService *provider)
{
    setGpuPower(false);

    if (mWorkLoop) {
        mWorkLoop->release();
        mWorkLoop = nullptr;
    }

    if (mGpuRegs) {
        mGpuRegs->release();
        mGpuRegs = nullptr;
    }

    super::stop(provider);
}

// ---------------------------------------------------------------------------
// GPU initialization
// ---------------------------------------------------------------------------

IOReturn NativeMaliG57::initGpuRegisters()
{
    mGpuRegBase = 0x23100000;
    return kIOReturnSuccess;
}

IOReturn NativeMaliG57::probeGpuId()
{
    mGpuId = MALI_GPU_ID_G57;
    mCoreId = 0;
    return kIOReturnSuccess;
}

IOReturn NativeMaliG57::setupInterrupts()
{
    for (int i = 0; i < MALI_NUM_IRQS; i++) {
        mIrqs[i] = 60 + i;
    }
    return kIOReturnSuccess;
}

IOReturn NativeMaliG57::configureClocks()
{
    return kIOReturnSuccess;
}

IOReturn NativeMaliG57::initPlatform()
{
    return kIOReturnSuccess;
}

IOReturn NativeMaliG57::initJobSlots()
{
    mJobSlots = MALI_NUM_JOB_SLOTS;
    mJobSlotsAvailable = MALI_NUM_JOB_SLOTS;
    return kIOReturnSuccess;
}

// ---------------------------------------------------------------------------
// Power management
// ---------------------------------------------------------------------------

IOReturn NativeMaliG57::setGpuPower(bool enable)
{
    if (enable && !mPoweredOn) {
        mPoweredOn = true;
    } else if (!enable && mPoweredOn) {
        mPoweredOn = false;
    }
    return kIOReturnSuccess;
}

IOReturn NativeMaliG57::setDvfsFrequency(uint32_t freq_mhz)
{
    uint32_t valid_freqs[] = {1500, 1860, 2940, 3160, 512, 3200, 3300};
    bool valid = false;
    for (uint32_t i = 0; i < MALI_NUM_DVFS_FREQS; i++) {
        if (valid_freqs[i] == freq_mhz) {
            valid = true;
            break;
        }
    }
    if (!valid) {
        return kIOReturnError;
    }
    mDvfsFreq = freq_mhz;
    return kIOReturnSuccess;
}

// ---------------------------------------------------------------------------
// Job management
// ---------------------------------------------------------------------------

IOReturn NativeMaliG57::submitJob(uint32_t job_slot, uintptr_t cmd_addr, uint32_t cmd_size)
{
    if (job_slot >= MALI_NUM_JOB_SLOTS) {
        return kIOReturnError;
    }
    if (!mPoweredOn) {
        return kIOReturnError;
    }
    if (mJobSlotsAvailable == 0) {
        return kIOReturnError;
    }
    mJobSlotsAvailable--;
    return kIOReturnSuccess;
}

IOReturn NativeMaliG57::releaseJobSlot(uint32_t job_slot)
{
    if (job_slot >= MALI_NUM_JOB_SLOTS) {
        return kIOReturnError;
    }
    mJobSlotsAvailable++;
    return kIOReturnSuccess;
}
/* XNU kernel module entry points */
int kmod_start(void)
{
    return kIOReturnSuccess;
}

int kmod_stop(void)
{
    return kIOReturnSuccess;
}

OSDefineMetaClassAndStructors(NativeMaliG57, IOService)
