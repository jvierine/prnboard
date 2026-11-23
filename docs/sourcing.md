# Initial sourcing check — 23 November 2026

Public catalogue evidence only; not a reservation or a complete current assembly quote. Search-index quantities can lag actual order availability. Recheck in a BOM quotation before ordering. LCSC stock is not equivalent to JLC assembly stock.

| Part | JLC code | Observed listing | Draft treatment |
| --- | --- | --- | --- |
| ESP32-S3-WROOM-1-N8 | C2913198 | 2874 shown; $4.216 at 10; Standard assembly only | Wi-Fi candidate |
| MAX-M10S-00B | C4153167 | 761 shown; $10.5062 at 10 | Single-frequency fallback |
| AD9850BRSZ | C18731 | DDS category showed 57; $21.6148 single | 100 MHz DDS candidate; modest stock needs recheck |
| SI5351C-B-GM | C3608122 | Catalogue/search showed 66; current order quantity/price not established | $6 allowance, pending sourcing and electrical review |
| KDS 1XTV10000MDA | C253701 | Listing found; current order quantity/price not established | $1.10 allowance, exact footprint review required |
| NEO-F10N-00B-20 | Not established | Exact raw-data variant not found in JLC search | Optional TEC upgrade, not populated |
| Generic NEO-F10N-00B | C9900110343 | Zero stock; variant not qualified | Do not substitute for raw-data variant |
| Quectel LG290P03AAMD | C29781241 / C23046224 | Listings found; stock/price not established | TEC candidate, not populated |
| Generic LC29H | C9900022933 | Zero stock; variant unspecified | Not selected |

The AD9834B's vendor clock limit is 50 MHz despite some catalogue descriptions saying 75 MHz; do not use it for 30 MHz output or clock it at 75 MHz. The C grade is rated 75 MHz, but economical JLC stock was not established.

Sources:

- [ESP32-S3 JLC listing](https://jlcpcb.com/partdetail/3198296-ESP32_S3_WROOM_1N8/C2913198)
- [MAX-M10S JLC listing](https://jlcpcb.com/partdetail/U_BLOXAG-MAX_M10S00B/C4153167)
- [AD9850 JLC listing](https://jlcpcb.com/partdetail/AnalogDevices-AD9850BRSZ/C18731)
- [JLC DDS catalogue](https://jlcpcb.com/parts/2nd/Data_Acquisition/Direct_Digital_Synthesis_%28DDS%29_3144)
- [Si5351C JLC listing](https://jlcpcb.com/partdetail/SkyworksSolutions-SI5351C_BGM/C3608122)
- [KDS JLC listing](https://jlcpcb.com/partdetail/KDSDaishinku-1XTV10000MDA/C253701)
- [LG290P JLC listing](https://jlcpcb.com/partdetail/Quectel-LG290P03AAMD/C29781241)
- [LC29H JLC listing](https://jlcpcb.com/partdetail/JLCPCBAssembly-LC29H/C9900022933)
- [Quectel observation-message protocol](https://www.quectel.com/content/uploads/2024/09/Quectel_LG290P03LGx80P03_GNSS_Protocol_Specification_V1.1.pdf)
- [AD9850 datasheet](https://www.analog.com/media/en/technical-documentation/data-sheets/AD9850.pdf)
- [AD9834 datasheet and grade limits](https://www.analog.com/media/en/technical-documentation/data-sheets/AD9834.pdf)
- [Si5351 datasheet](https://www.skyworksinc.com/-/media/SkyWorks/SL/documents/public/data-sheets/Si5351-B.pdf)
- [JLC sourcing and consignment options](https://jlcpcb.com/help/article/pcba-parts-sourcing-instruction)

KiCad-derived footprint/symbol information follows the KiCad library licensing terms: [CC BY-SA 4.0 with library exception](https://www.kicad.org/libraries/license/). Generated CAD is an engineering draft and must be reviewed against manufacturer drawings.
