# Source-only Measurement Alignment and Sampling Audit

Generated: 2026-07-25T05:23:11.259158+00:00

## Scope

- Source logical path: `../../data/USROP`
- Files: 7
- Rows: 198,928
- Layer D outcome access: none
- Required columns: Measured Depth m, Weight on Bit kkgf, Average Rotary Speed rpm, Average Standpipe Pressure kPa, Rate of Penetration m/h

## Sampling geometry

- Positive consecutive MD gaps: 198,917
- Median gap: 0.033000 m
- 99th percentile: 0.195000 m
- 99.9th percentile: 0.609000 m
- Maximum: 166.497000 m
- Gaps greater than 1.0 m: 128
- Segments under the frozen 1.0 m break rule: 135
- Valid segment span median: 4.270 m

## Frozen parameter basis

1. `g_max = 1.0 m`. This is above the source 99.9th-percentile native gap
   while breaking the sparse large discontinuities instead of assigning them
   depth weight.
2. `w_max = 0.5 m`. This bounds any single native record's representative
   interval to half of the segment-breaking gap and prevents endpoint or
   locally sparse records from dominating the loss.
3. Minimum segment size is two unique MD points, the minimum needed to define
   a positive represented interval.
4. Minimum family scoring coverage is 100 m, with at least 100 scoring points
   and one valid segment. These are engineering precision/coverage guards,
   not model-performance thresholds.
5. Fixed-depth sensitivity uses 1.0 m blocks anchored at 0.0 m, requires at
   least 0.5 m represented coverage per block, and introduces no interpolation.
6. Native co-sampled rows are the primary alignment unit. Cross-file fuzzy
   matching, time joins, and pre-prediction resampling are excluded.

## ROP semantic observations

- Source ROP missing/non-finite values are reported in the file audit.
- Non-positive source ROP count: 0.
- No upper ROP threshold was selected from source outcomes; the primary
  protocol retains finite positive extremes and reports them.

These choices were made without Layer D ROP or performance feedback.
