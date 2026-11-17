# Agent instructions

This repository owns shared Unisoc UMS9230 / Tiger T606 platform support for
UniXNU board ports. Keep SoC operations here; board wiring/policy lives in
the device repository (hawaii-unixnu).

Read these UniXNU pages before editing:

1. [Porting](https://unixnu.com/porting/)
2. [SoC support](https://unixnu.com/porting/soc-support)
3. [Device repositories](https://unixnu.com/porting/device-repository)
4. [Device trees](https://unixnu.com/porting/device-tree)
5. [Driver matching](https://unixnu.com/drivers/device-tree-matching)

Rules specific to this repository:

- The target is Mach-O. Inline assembly goes through the Darwin assembler,
  where `;` starts a comment. Separate instructions with `"\n\t"` and check
  the object with `llvm-objdump --disassemble-symbols`.
- A node reaches the Apple device tree only with `unixnu,adt-name` and
  `status` other than `disabled`. Do not add `unixnu,cluster-type` or
  `virtual-timer-intid`; the working kernel runs without them.
- XNU patches apply with plain `git apply` in series order, after the ARM64
  series and before the OS and device series. Check new patches against a
  fresh XNU clone.
- Do not use observations from other Unisoc SoCs to decide UMS9230 behavior.
- Keep addresses, hostnames, accounts, and local paths out of this repository.

Report commands, results, required local inputs, and hardware checkpoints.
Write concise English describing current behavior.
