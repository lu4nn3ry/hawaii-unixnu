#ifndef NATIVE_MALI_G57_H
#define NATIVE_MALI_G57_H

/*
 * NativeMaliG57.h — Mali-G57 (Valhall) driver definitions for XNU on UMS9230.
 *
 * Source: Mali kbase r28p0-01eac0 DDK + qogirl6 platform glue
 *   patches 0014-0017 in CreitinGameplays/motorola-moto-e32-root/
 *   patches/kernel-sprd/branch-hawaii-diag/
 *
 * Vendor DT node (from live DT proc_device_tree_root/sprd-marlin3/):
 *   compatible = "sprd,mali-natt"
 *   reg = 0x23100000 / 0x100000
 *   interrupts = GIC_SPI 60 x3 (JOB/MMU/GPU)
 *   DVFS operating-points = [1500, 1860, 1500, 2940, 3160, 2940, 512, 3200, 3300] MHz
 *   gpu-supply = phandle 0x21
 *   nvmem-cell = gpu_bin (phandle 0x25)
 */

#include <stdint.h>
#include <stddef.h>
#include <stdbool.h>

/* GPU identification */
#define MALI_G57_GPU_ID_MASK      0xFFF0
#define MALI_G57_GPU_ID           0xF570
#define MALI_G57_REVISION_MASK    0x000F

/* Register offsets (from r28p0 DDK / vendor kernel) */
#define MALI_REG_GPU_ID           0x0000
#define MALI_REG_IRQ_RAW          0x0010
#define MALI_REG_IRQ_CLEAR        0x0014
#define MALI_REG_IRQ_MASK         0x0018
#define MALI_REG_CORE_ID          0x00E0
#define MALI_REG_CORE_TOP         0x0100
#define MALI_REG_L2_CTRL          0x0120
#define MALI_REG_PWR_CTRL         0x0140
#define MALI_REG_IRQ_PENDING      0x0020

/* GPU IRQ lines (from vendor DT) */
#define MALI_IRQ_JOB              0
#define MALI_IRQ_MMU              1
#define MALI_IRQ_GPU              2
#define MALI_NUM_IRQS             3

/* Power control values */
#define MALI_PWR_CTRL_ON          0x1
#define MALI_PWR_CTRL_OFF         0x0

/* DVFS operating points from vendor DT (MHz) */
#define MALI_DVFS_NUM_LEVELS      9
extern const uint32_t mali_dvfs_levels[MALI_DVFS_NUM_LEVELS];

/* GPU memory regions */
#define MALI_GPU_REG_BASE         0x23100000
#define MALI_GPU_REG_SIZE         0x100000

/* Interrupt number from vendor DT */
#define MALI_GPU_IRQ              60   /* GIC_SPI */

/* kbase context flags */
#define MALI_CTX_FLAG_INITED      0x1
#define MALI_CTX_FLAG_POWERED     0x2
#define MALI_CTX_FLAG_CLOCKED     0x4

/* Platform data from DT */
struct mali_g57_platform_data {
    uintptr_t reg_base;
    uint32_t reg_size;
    uint32_t irq_base;
    uint32_t num_irqs;
    uint32_t dvfs_levels[MALI_DVFS_NUM_LEVELS];
    uint32_t num_dvfs_levels;
    const char *compatible;
    bool has_power_domain;
    bool has_clock_gating;
};

/* Runtime state */
struct mali_g57_runtime {
    uint32_t flags;
    uint32_t gpu_id;
    uint32_t revision;
    uint32_t current_freq_mhz;
    bool powered_on;
    bool clocked;
    void *reg_base;          /* IO-mapped register base */
    void *workloop;          /* IOWorkLoop for interrupts */
    void *irq_sources[MALI_NUM_IRQS];
};

/* Function prototypes */
int mali_g57_probe(struct mali_g57_platform_data *pdata,
                   struct mali_g57_runtime *rt);
int mali_g57_remove(struct mali_g57_runtime *rt);
int mali_g57_power_on(struct mali_g57_runtime *rt);
int mali_g57_power_off(struct mali_g57_runtime *rt);
int mali_g57_set_dvfs(struct mali_g57_runtime *rt, uint32_t freq_mhz);
uint32_t mali_g57_read_reg(struct mali_g57_runtime *rt, uint32_t offset);
void mali_g57_write_reg(struct mali_g57_runtime *rt, uint32_t offset, uint32_t val);
void mali_g57_irq_handler(void *rt, int irq);

#endif /* NATIVE_MALI_G57_H */
