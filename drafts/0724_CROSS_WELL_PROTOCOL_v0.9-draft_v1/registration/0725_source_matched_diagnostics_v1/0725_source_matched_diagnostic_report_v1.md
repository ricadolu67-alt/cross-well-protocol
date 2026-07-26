# Source-only matched falsification diagnostics

- Status: `PASS`
- Layer D numeric outcome access: `NONE`
- Split fits recorded: 25
- Dependence fits recorded: 20
- F-15 semantic track: retrospective failure analysis only

## Mean paired distortions (MAE condition A minus condition B)

| diagnostic   | case_id     | mechanism_isolated   |   repetitions |   mean_distortion |   median_distortion |   min_distortion |   max_distortion |   positive_fraction |
|:-------------|:------------|:---------------------|--------------:|------------------:|--------------------:|-----------------:|-----------------:|--------------------:|
| dependence   | DEP_F15F15S | False                |             5 |          3.43678  |            3.37293  |         2.25519  |        4.55871   |                 1   |
| dependence   | DEP_F15F15S | True                 |             5 |          3.93674  |            3.72322  |         3.13661  |        4.71969   |                 1   |
| dependence   | DEP_F7F9    | False                |             5 |         12.9998   |           12.8924   |        11.882    |       14.4095    |                 1   |
| dependence   | DEP_F7F9    | True                 |             5 |         12.6473   |           12.4253   |        11.7562   |       13.9093    |                 1   |
| split        | SPLIT_F14   | True                 |             5 |          0.310989 |            0.427113 |        -1.25409  |        1.27543   |                 0.6 |
| split        | SPLIT_F15   | True                 |             5 |          4.43113  |            4.17424  |         3.2564   |        5.67602   |                 1   |
| split        | SPLIT_F5    | True                 |             5 |          1.90205  |            1.70182  |         1.21523  |        2.85246   |                 1   |
| split        | SPLIT_F7F9  | True                 |             5 |          8.67972  |            8.83568  |         7.239    |        9.37988   |                 1   |
| split        | SPLIT_F9A   | True                 |             5 |         -0.336743 |           -0.422282 |        -0.612586 |        0.0900003 |                 0.2 |

Positive values denote the prespecified optimistic shift for split/dependence contrasts.
These identified cases do not estimate a petroleum-wide average bias.
