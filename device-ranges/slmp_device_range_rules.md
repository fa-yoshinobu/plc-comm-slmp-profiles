# SLMP Device Range Rule Definition

This is the editable source for `slmp_device_range_rules.json`.
Run `python tools/generate_device_range_rules.py` after editing this file.

## Metadata

| Item | Value |
| --- | --- |
| schema_version | 1 |
| date | 2026-07-03 |
| description | Rules for SLMP device range discovery from SD block reads. Generated from device-ranges/slmp_device_range_rules.md. |

## Value Kinds

| Kind | Meaning |
| --- | --- |
| fixed | Use fixed_value as the point count without reading SD. |
| word | Use the 16-bit value at SDn as the point count. |
| dword | Use the 32-bit value at SDn..SDn+1 as the point count. |
| word-clipped | Clip the 16-bit value to the given limit. |
| dword-clipped | Clip the 32-bit value to the given limit. |
| unsupported | This family does not exist in this profile. |
| undefined | No finite upper-bound register is defined; handle through runtime probes or equivalent logic. |

## Device Families

| Classification | Symbol | Device name | Type | Notation |
| --- | --- | --- | --- | --- |
| User device | X | Input | bit | base16 |
| User device | Y | Output | bit | base16 |
| User device | M | Internal relay | bit | base10 |
| User device | B | Link relay | bit | base16 |
| User device | F | Annunciator | bit | base10 |
| User device | SB | Link special relay | bit | base16 |
| User device | V | Edge relay | bit | base10 |
| User device | S | Step relay | bit | base10 |
| User device | T | Timer | TS:bit, TC:bit, TN:word | base10 |
| User device | ST | Retentive timer | STS:bit, STC:bit, STN:word | base10 |
| User device | LT | Long timer | LTS:bit, LTC:bit, LTN:dword | base10 |
| User device | LST | Long retentive timer | LSTS:bit, LSTC:bit, LSTN:dword | base10 |
| User device | C | Counter | CS:bit, CC:bit, CN:word | base10 |
| User device | LC | Long counter | LCS:bit, LCC:bit, LCN:dword | base10 |
| User device | D | Data register | word | base10 |
| User device | W | Link register | word | base16 |
| User device | SW | Link special register | word | base16 |
| User device | L | Latch relay | bit | base10 |
| System Device | SM | Special relay | bit | base10 |
| System Device | SD | Special register | word | base10 |
| Link Direct Device | Jn\X | Link input | bit | base16 |
| Link Direct Device | Jn\Y | Link output | bit | base16 |
| Link Direct Device | Jn\B | Link relay | bit | base16 |
| Link Direct Device | Jn\SB | Link special relay | bit | base16 |
| Link Direct Device | Jn\W | Link register | word | base16 |
| Link Direct Device | Jn\SW | Link special register | word | base16 |
| Module access device | Un\G | Module access device | word | base10 |
| CPU buffer memory access device | U3En\G | CPU buffer memory access device | word | base10 |
| CPU buffer memory access device | U3En\HG | CPU buffer memory access device | word | base10 |
| Index register | Z | Index register | word | base10 |
| Index register | LZ | Long index register | dword | base10 |
| File register | R | File register | word | base10 |
| File register | ZR | File register | word | base10 |
| Refresh data register | RD | Refresh data register | word | base10 |

## Notation Overrides

| Profile | Device family | Notation |
| --- | --- | --- |
| melsec:iq-f | X | base8 |
| melsec:iq-f | Y | base8 |

## Runtime Probe Metadata

| Item | Value |
| --- | --- |
| reason | Some Q-series devices do not have their ranges written into SD registers by the PLC, so SD reads alone cannot determine the range. Find boundaries by probing whether reads succeed. |
| applies_to | melsec:lcpu, melsec:qcpu, melsec:qnu, melsec:qnudv |
| max_probe_count | 1048576 |
| probe_read | Read one word at the target address; treat any SLMP error as unreadable. |
| source_note | Record probe results in the catalog with source='Runtime access check'. |

## Runtime Probe Steps

| Order | Profiles | Family | Method | Parameters | Spec |
| --- | --- | --- | --- | --- | --- |
| 1 | melsec:qcpu | Z | single-address-check | check_address=15; readable_count=16; unreadable_count=10 | If Z15 is readable, the point count is 16; otherwise it is 10. |
| 2 | melsec:lcpu, melsec:qcpu, melsec:qnu, melsec:qnudv | ZR | doubling-then-binary-search | - | If ZR0 is not readable, the point count is 0. If it is readable, start high at 1 and advance with (high*2)+1 until reads fail, capped at max_probe_count-1. Then binary-search low..high and use the maximum readable address plus 1 as the point count. If the capped address is readable, use max_probe_count. |
| 3 | melsec:lcpu, melsec:qcpu, melsec:qnu, melsec:qnudv | R | derived | source_family=ZR; max_value=32768 | Use min(probed ZR point count, 32768) as the R point count. |

## Profile Blocks

| Profile | Register start | Register count |
| --- | --- | --- |
| melsec:iq-r | 260 | 50 |
| melsec:iq-l | 260 | 50 |
| melsec:mx-f | 260 | 50 |
| melsec:mx-r | 260 | 50 |
| melsec:iq-f | 260 | 46 |
| melsec:qcpu | 290 | 15 |
| melsec:lcpu | 286 | 26 |
| melsec:qnu | 286 | 26 |
| melsec:qnudv | 286 | 26 |

## Rule Matrix

| Device family | melsec:iq-r | melsec:iq-l | melsec:mx-f | melsec:mx-r | melsec:iq-f | melsec:qcpu | melsec:lcpu | melsec:qnu | melsec:qnudv |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| X | dword; source=SD260 | dword; source=SD260 | dword; source=SD260 | dword; source=SD260 | dword; source=SD260 | word; source=SD290 | word; source=SD290 | word; source=SD290 | word; source=SD290 |
| Y | dword; source=SD262 | dword; source=SD262 | dword; source=SD262 | dword; source=SD262 | dword; source=SD262 | word; source=SD291 | word; source=SD291 | word; source=SD291 | word; source=SD291 |
| M | dword; source=SD264 | dword; source=SD264 | dword; source=SD264 | dword; source=SD264 | dword; source=SD264 | word-clipped=32768; source=SD292 | dword; source=SD286 | dword; source=SD286 | dword; source=SD286 |
| B | dword; source=SD266 | dword; source=SD266 | dword; source=SD266 | dword; source=SD266 | dword; source=SD266 | word-clipped=32768; source=SD294 | dword; source=SD288 | dword; source=SD288 | dword; source=SD288 |
| SB | dword; source=SD268 | dword; source=SD268 | dword; source=SD268 | dword; source=SD268 | dword; source=SD268 | word; source=SD296 | word; source=SD296 | word; source=SD296 | word; source=SD296 |
| F | dword; source=SD270 | dword; source=SD270 | dword; source=SD270 | dword; source=SD270 | dword; source=SD270 | word; source=SD295 | word; source=SD295 | word; source=SD295 | word; source=SD295 |
| V | dword; source=SD272 | dword; source=SD272 | dword; source=SD272 | dword; source=SD272 | unsupported | word; source=SD297 | word; source=SD297 | word; source=SD297 | word; source=SD297 |
| L | dword; source=SD274 | dword; source=SD274 | dword; source=SD274 | dword; source=SD274 | dword; source=SD274 | word; source=SD293 | word; source=SD293 | word; source=SD293 | word; source=SD293 |
| S | dword; source=SD276 | dword; source=SD276 | dword; source=SD276 | dword; source=SD276 | dword; source=SD276 | word; source=SD298 | word; source=SD298 | word; source=SD298 | word; source=SD298 |
| D | dword; source=SD280 | dword; source=SD280 | dword; source=SD280 | dword; source=SD280 | dword; source=SD280 | word-clipped=32768; source=SD302 | dword; source=SD308 | dword; source=SD308 | dword; source=SD308 |
| W | dword; source=SD282 | dword; source=SD282 | dword; source=SD282 | dword; source=SD282 | dword; source=SD282 | word-clipped=32768; source=SD303 | dword; source=SD310 | dword; source=SD310 | dword; source=SD310 |
| SW | dword; source=SD284 | dword; source=SD284 | dword; source=SD284 | dword; source=SD284 | dword; source=SD284 | word; source=SD304 | word; source=SD304 | word; source=SD304 | word; source=SD304 |
| R | dword-clipped=32768; source=SD306 | dword-clipped=32768; source=SD306 | dword-clipped=32768; source=SD306 | dword-clipped=32768; source=SD306 | dword; source=SD304 | fixed=32768; probe | dword; source=SD306; probe | dword; source=SD306; probe | dword; source=SD306; probe |
| T | dword; source=SD288 | dword; source=SD288 | dword; source=SD288 | dword; source=SD288 | dword; source=SD288 | word; source=SD299 | word; source=SD299 | word; source=SD299 | word; source=SD299 |
| ST | dword; source=SD290 | dword; source=SD290 | dword; source=SD290 | dword; source=SD290 | dword; source=SD290 | word; source=SD300 | word; source=SD300 | word; source=SD300 | word; source=SD300 |
| C | dword; source=SD292 | dword; source=SD292 | dword; source=SD292 | dword; source=SD292 | dword; source=SD292 | word; source=SD301 | word; source=SD301 | word; source=SD301 | word; source=SD301 |
| LT | dword; source=SD294 | dword; source=SD294 | dword; source=SD294 | dword; source=SD294 | unsupported | unsupported | unsupported | unsupported | unsupported |
| LST | dword; source=SD296 | dword; source=SD296 | dword; source=SD296 | dword; source=SD296 | unsupported | unsupported | unsupported | unsupported | unsupported |
| LC | dword; source=SD298 | dword; source=SD298 | dword; source=SD298 | dword; source=SD298 | dword; source=SD298 | unsupported | unsupported | unsupported | unsupported |
| Z | word; source=SD300 | word; source=SD300 | word; source=SD300 | word; source=SD300 | word; source=SD300 | fixed=10; probe | fixed=20 | fixed=20 | fixed=20 |
| LZ | word; source=SD302 | word; source=SD302 | word; source=SD302 | word; source=SD302 | word; source=SD302 | unsupported | unsupported | unsupported | unsupported |
| ZR | dword; source=SD306 | dword; source=SD306 | dword; source=SD306 | dword; source=SD306 | unsupported | undefined; probe | dword; source=SD306; probe | dword; source=SD306; probe | dword; source=SD306; probe |
| RD | dword; source=SD308 | dword; source=SD308 | dword; source=SD308 | dword; source=SD308 | unsupported | unsupported | unsupported | unsupported | unsupported |
| SM | fixed=4096 | fixed=4096 | fixed=10000 | fixed=4496 | fixed=10000 | fixed=1024 | fixed=2048 | fixed=2048 | fixed=2048 |
| SD | fixed=4096 | fixed=4096 | fixed=10000 | fixed=4496 | fixed=12000 | fixed=1024 | fixed=2048 | fixed=2048 | fixed=2048 |
