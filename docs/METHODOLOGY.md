# Methodology & assumptions

All defaults live in `web/engine.js` (`CATS`, `DEFAULTS`) and most are editable in the viewer's *Design assumptions* panel. Code references are the basis used for DD sizing and must be verified against the editions in force at filing.

## Spaces

| Space | Occupant load (ft²/p) | Rp / Ra (ventilation) | Lighting / plug (W/ft²) | Sprinkler hazard | Notes |
|---|---|---|---|---|---|
| Exhibition gallery | 30 gross | 7.5 / 0.06 | 1.0 / 1.5 | Light | open plan, supply grid |
| Immersive hall | 15 net | 7.5 / 0.06 | 0.3 / 1 + AV | Light | 360° projection, see below |
| Auditorium | 7 net | 5 / 0.06 | 0.8 / 4 | Light | |
| Food court / events | 15 net | 7.5 / 0.18 | 0.8 / 8 | Ordinary 1 | kitchen fixtures TBD |
| Lobby / café | 15 net | 5 / 0.06 | 0.8 / 1.5 | Light | open plan |
| Shop / library | 60 gross | 7.5 / 0.12 | 1.1 / 2 | Ordinary 2 | |
| Offices | 100 gross | 5 / 0.06 | 0.64 / 0.25 + desks | Light | 1 desk / 10 m², 150 W each |

Occupant loads follow NYC BC Table 1004.5 (egress basis, conservative for ventilation). Ventilation: NYC MC §403 / ASHRAE 62.1 ventilation rate procedure, Ez = 0.8.

## HVAC
- Sensible load = envelope (Btuh/ft²) + people + lighting + plug/AV; supply air at ΔT 20 °F, minimum 0.4 cfm/ft².
- Concepts: **DOAS (ERV) on roof + floor-by-floor AHUs** with CHW/HHW risers (default), or **central roof AHUs** with supply/return shafts.
- Mains 1500 fpm, branches 900 fpm, risers 2000 fpm; max duct depth 30 in.
- Open-plan spaces get run-out grids every 6 m; multi-storey halls are served at their own ceiling.
- Plant: air-cooled/heat-recovery chillers (N+1), air-to-water heat pumps (all-electric, LL97), DOAS, pumps — packed into the roof technical space with 1 m clearance; pumps move to the basement if the roof is full.

## Immersive halls
- Projector columns = wall perimeter / (image width × (1 − overlap)); tiers = 90% of wall height / (image height × (1 − overlap)).
- Defaults: 8 × 5 m image, 15% edge blend, 2 kW per laser projector (~30k lm), 8 kW AV rack per hall.
- Supply diffusers inset ~4 m from projection walls, no sidewall grilles; high-level return over the projector ring.

## Plumbing
- Fixtures provided are counted from the restroom model; required per NYC PC Table 403.1 (50/50 split, no urinal substitution).
- WSFU → gpm with the flush-valve Hunter curve; stacks per NYC PC Table 710.1(1); storm leaders per §1106 using the input rainfall rate.
- Domestic water: street pressure (assumed 45 psi) vs 25 psi at flush valves + elevation + friction + meter/RPZ → booster set in the basement and pressure zones ≤ 80 psi.

## Electrical
- Connected load = lighting + plug/AV + HVAC (chillers, fans, pumps) + elevators + fire pump; demand factor 0.8, 25% spare, 480Y/277 V.
- Generator sized for life-safety and legally required standby loads (egress lighting, fire alarm, smoke control, fire pump, fire service elevator).

## Fire protection
- Sprinkler spacing 15 ft (light hazard) / 12 ft (ordinary); heads only where the slab exists.
- One 6 in combined standpipe per modelled stair; fire pump flow 500 gpm + 250 gpm per additional standpipe (max 1000), 100 psi at the top outlet.

## Shafts
- Risers are laid out in rows along the modelled shaft; a 10% allowance is added for access and fire-stopping.
- If risers do not fit, the shaft grows (southward) and the check reports the new outline to update in Rhino.

## Open inputs (highest impact first)
1. Floor AHU rooms and stacked electrical closets next to the main shaft.
2. Real design occupancy and AV equipment per immersive hall (projector model, throw, floor projection).
3. Floor-to-floor heights and structure depth (current clear height ≈ 2.7 m under services on 5 m floors).
4. Restroom strategy (L01 short of WCs, none on L11, drinking fountains).
5. Utility points of entry (street frontage for power, water, sewer, fire service).
6. Collections environmental classes, envelope performance, life-safety power strategy, code editions at filing.
