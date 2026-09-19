# 冻结候选池稳健性分析报告 v2

评分前守卫全部通过：签名与输入、源队列/训练行、训练路径、23/21/19/8队列计数、原主增益和t区间、MD-only场级效应。10个MLP seed均有ConvergenceWarning并达到80次迭代，未重跑或增加迭代。所有相关结果行标注警告。输出自检不是独立科学验收。

The eight candidate configurations were frozen in the formal Layer A manifest before Layer D outcome access. The decision to score all eight on Layer D was made after Layer D outcomes were known; the timestamp on this contract constrains subsequent analyst degrees of freedom but does not make this comparison outcome-naive.

这是解锁后合同固定的探索性分析，不替换注册主估计量。HistGB为冻结配置在解锁后统一源域中位数插补下的表现，不称冻结HistGB管线。正增益表示候选MAE更低；随机候选先算各seed家族MAE再等权平均。以下区间均为8油田的描述性t区间，不作确认性p值或多重比较推断。

## 完整固定对比

| 候选 | 对比 | 均值 m/h | 95% t区间 | 正方向场数 | LOFO方向 | 警告seed数 |
|---|---|---:|---|---:|---|---:|
| Ridge_alpha_1 | c_vs_md_only | -0.879896 | [-1.739183, -0.020610] | 1/8 | 全部同号 | 0 |
| Ridge_alpha_1 | c_vs_source_median | 1.359861 | [-0.794945, 3.514668] | 5/8 | 全部同号 | 0 |
| Ridge_alpha_1 | c_vs_frozen_et | -0.712007 | [-2.150817, 0.726803] | 4/8 | 全部同号 | 0 |
| Ridge_alpha_100 | c_vs_md_only | -0.866168 | [-1.741895, 0.009558] | 1/8 | 全部同号 | 0 |
| Ridge_alpha_100 | c_vs_source_median | 1.373590 | [-0.746561, 3.493741] | 5/8 | 全部同号 | 0 |
| Ridge_alpha_100 | c_vs_frozen_et | -0.698279 | [-2.107148, 0.710590] | 4/8 | 全部同号 | 0 |
| HistGB_lr005_leaf15 | c_vs_md_only | -1.488668 | [-2.807061, -0.170276] | 2/8 | 全部同号 | 0 |
| HistGB_lr005_leaf15 | c_vs_source_median | 0.751089 | [-1.057609, 2.559788] | 6/8 | 全部同号 | 0 |
| HistGB_lr005_leaf15 | c_vs_frozen_et | -1.320779 | [-2.278427, -0.363131] | 0/8 | 全部同号 | 0 |
| HistGB_lr008_leaf31 | c_vs_md_only | -2.147432 | [-3.652348, -0.642515] | 0/8 | 全部同号 | 0 |
| HistGB_lr008_leaf31 | c_vs_source_median | 0.092326 | [-1.380157, 1.564810] | 6/8 | 并非全部同号 | 0 |
| HistGB_lr008_leaf31 | c_vs_frozen_et | -1.979542 | [-2.699814, -1.259271] | 0/8 | 全部同号 | 0 |
| ExtraTrees_depth12_leaf30 | c_vs_md_only | -0.413716 | [-2.026287, 1.198856] | 4/8 | 全部同号 | 0 |
| ExtraTrees_depth12_leaf30 | c_vs_source_median | 1.826042 | [0.748837, 2.903247] | 7/8 | 全部同号 | 0 |
| ExtraTrees_depth12_leaf30 | c_vs_frozen_et | -0.245826 | [-0.408995, -0.082658] | 1/8 | 全部同号 | 0 |
| ExtraTrees_depth18_leaf100 | c_vs_md_only | -0.167889 | [-1.800865, 1.465087] | 4/8 | 并非全部同号 | 0 |
| ExtraTrees_depth18_leaf100 | c_vs_source_median | 2.071869 | [1.024861, 3.118876] | 8/8 | 全部同号 | 0 |
| ExtraTrees_depth18_leaf100 | c_vs_frozen_et | 0.000000 | [0.000000, 0.000000] | 0/8 | 自比较：恒等为零 | 0 |
| MLP_64_32 | c_vs_md_only | -3.680446 | [-6.088552, -1.272340] | 0/8 | 全部同号 | 5 |
| MLP_64_32 | c_vs_source_median | -1.440688 | [-3.829666, 0.948290] | 3/8 | 全部同号 | 5 |
| MLP_64_32 | c_vs_frozen_et | -3.512557 | [-5.501937, -1.523176] | 0/8 | 全部同号 | 5 |
| MLP_96_48 | c_vs_md_only | -3.364916 | [-4.981421, -1.748411] | 0/8 | 全部同号 | 5 |
| MLP_96_48 | c_vs_source_median | -1.125158 | [-2.359085, 0.108768] | 1/8 | 全部同号 | 5 |
| MLP_96_48 | c_vs_frozen_et | -3.197027 | [-3.954626, -2.439428] | 0/8 | 全部同号 | 5 |

## 按预定规则解读

焦点比较：八个候选相对MD-only Ridge的油田等权均值均为负，没有候选的95% t区间下限大于零。因此，在该解锁后探索性面板中，冻结池内没有候选建立超出MD-only比较器的油田等权均值优势。不能将此写成模型等效、操作变量没有物理作用或复杂模型普遍无价值。

相对SourceMedian，只有两个ExtraTrees配置的区间下限大于零：depth18/leaf100在8/8场为正，depth12/leaf30在7/8场为正，两者LOFO均保持正向。其余配置即使方向在多数场为正，也未建立该均值优势。

所有其他候选相对冻结ExtraTrees的均值均为负；这支持冻结选择在本候选池和本队列中的相对位置，但不证明ExtraTrees是ROP最优学习器。两项MLP结论尤其受固定80次迭代与全部seed不收敛警告限制，只能描述这两个冻结配置。

源域排名和Layer D排名呈较高描述性一致性：逐外折worst-2排名平均值的Spearman为0.904762，平均单元MAE排名平均值为0.886243。源域排名完整逐折表及计算定义保留；该结果不是预期必须出现的排名反转，不用于重新选择模型。

## 执行偏差与修复

1. 原定位守卫因R3包中的同内容loader复制件停止。按用户确认签名发布v2修订，原路径/完整哈希绑定不变，所有同名文件按哈希记录与核查。
2. 实现v2将MD-only预测命名为md，与原score_family内部深度键冲突。原结果守卫捕获后停止，未产生新候选预测；实现v3改为md_only_ridge并加冲突检查，所有守卫重新通过。原评分函数、数据、候选、容差均未改。
3. 首版汇总中冻结ET自比较因重复预测与不同浮点汇总路径产生约1e-15尾数，影响“正方向场数”的机械计数。v2汇总对所有c_vs_frozen_et复用同一候选家族/场损失作为冻结ET参照，自比较严格为零；未重拟合、重预测或改统计容差。最大场级变化为2.1316282072803006e-14 m/h。旧表与旧执行清单保留，v2表为报告使用版本；自比较不宣称方向稳健性。

## 追溯

合同tag：xw-audit-learner-pool-contract-v1和xw-audit-learner-pool-contract-v2。v2 commit：2ef0f3a675e0eec2c4b91810041dc8e7da9a3a9a。原输出与哈希在0918_执行清单_v1.json，后继表与哈希在0919_报告后继清单_v2.json。源域排名沿用0918_源域与LayerD排名并列_v1.csv及0918_源域逐外折排名_v1.csv。MLP每seed迭代数、训练损失、验证分数及警告见fit日志。
