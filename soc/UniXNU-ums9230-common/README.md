# UniXNU-ums9230-common: Shared Unisoc UMS9230 / Tiger T606 support

Shared SoC support for UniXNU board ports on the Unisoc UMS9230 (Tiger T606 /
`qogirl6`). Modelled on `UniXNU-sm8550-common` and `unixnu-eebbk-a2_x2-ums512`
(UMS512/T610, same SoC family).

This is a **bring-up skeleton**, not a working SoC support. No hardware result
yet.

## Repository layout

| Path | Purpose |
|------|---------|
| `AGENTS.md` | responsibilities and required reading |
| `README.md` | scope, inputs, build commands |
| `soc.toml` | format 2 SoC configuration |
| `configs/ums9230.config` | shared XNU kernel configuration |
| `dts/ums9230.dtsi` | shared device tree include |
| `patches/xnu/series` | ordered XNU patch series (empty until needed) |
| `kits/` | shared platform operations (placeholder) |

## Status

| Area | Status |
|------|--------|
| soc.toml | skeleton |
| configs/ums9230.config | skeleton |
| dts/ums9230.dtsi | skeleton (CPU, GIC, timer from UMS512 family) |
| patches/xnu/series | empty |
| kits | empty |

## License

BSD-2-Clause-Patent (same as UniXNU core).
