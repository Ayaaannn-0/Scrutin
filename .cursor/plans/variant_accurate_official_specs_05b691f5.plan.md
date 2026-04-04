# Variant Accurate Official Specs

## Goal
Make official specs precise per device variant so comparison quality improves, especially when API returns multiple options.

## Decisions Locked
- Battery: show official battery capacity only; no strict battery capacity compare from ADB.
- Variant selection: use ADB RAM + storage as primary selector.

## Files to update
- [c:\Users\ayaan\Scrutin\specs.py](c:\Users\ayaan\Scrutin\specs.py)
- [c:\Users\ayaan\Scrutin\app.py](c:\Users\ayaan\Scrutin\app.py)

## Implementation steps
1. In `specs.py`, add a normalization layer that extracts clean fields from API payload:
   - `battery_capacity` (e.g., `5000 mAh` only)
   - `display_resolution` (e.g., `1080 x 2400` only)
   - `storage_options_gb` (e.g., `[128, 256, 512]`)
   - `ram_options_gb` (e.g., `[8, 12]`)
   - `chipset_options` (list of variant chipsets)
2. Add variant picker in `specs.py`:
   - Parse ADB RAM total (e.g., `7.2 GB` -> nearest official RAM bucket `8`)
   - Parse ADB storage total (e.g., `108.7 GB` -> nearest official storage bucket `128`)
   - Select the closest official variant by RAM + storage distance score.
   - If ambiguous, keep `variant_confidence: low` and return conservative normalized values.
3. Return a stricter `official` object from `specs.py` for app consumption:
   - `battery` -> capacity only (`5000 mAh`)
   - `display` -> resolution only (`1080x2400` normalized)
   - `ram` -> selected variant RAM (`8 GB`)
   - `storage` -> selected variant storage (`128 GB`)
   - `chipset` -> best matching chipset line for selected variant
   - `variant_confidence` and `variant_reason` for transparency
4. In `app.py`, use returned normalized values directly in comparisons (no UI shape changes required).
5. Scoring safeguard in `app.py`:
   - if `variant_confidence` is low, reduce certainty (e.g., set comparison to `warn/unknown` where ambiguous) rather than claiming exact mismatch.
6. Validate with your current Motorola output and at least one other phone model.

## Expected result
- Official battery field becomes clean (`5000 mAh` not charging text).
- Display/storage comparisons use exact normalized values.
- Variant-specific matching is guided by ADB RAM/storage, improving accuracy when multiple official options exist.
