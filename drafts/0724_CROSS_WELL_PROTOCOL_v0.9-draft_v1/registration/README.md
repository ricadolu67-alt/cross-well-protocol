# Registration preparation

本目录仅用于准备后续的外部可信时间戳和公开复现材料。当前协议状态仍为
`v0.9-draft`，本目录中的文本不是已提交注册，也不得表述为 preregistration。

执行顺序固定为：

1. 完成 source-only / synthetic dry run；
2. 将全部未决参数替换为有依据的确定值；
3. `v1.0_freeze_checklist.csv` 全部 PASS；
4. 生成最终 SHA-256 manifest；
5. 在 ROP outcome 仍不可访问时提交 OSF Registration；
6. 创建 GitHub signed commit 与不可变 release，作为代码版本的第二证据；
7. 记录 OSF/GitHub 的 URL、时间和内容哈希；
8. 之后才可由协议指定的授权人执行 outcome unlock；
9. 最终公开复现包在研究完成后存入 Zenodo 并取得 DOI。

任何外部发布、注册、创建公开 release 或 DOI 的动作，都需要项目负责人在实际
提交前再次明确确认。
