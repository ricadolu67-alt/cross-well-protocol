# GitHub signed commit / immutable release checklist

当前项目 Git 工作区包含大量未跟踪的论文与数据文件，因此不得直接执行
`git add .`。v1.0 时应建立一个只包含可公开协议、代码、模型工件、清单和模板的
明确 allowlist；原始受限数据、个人路径、缓存、临时文件和 Layer D outcome
不得进入 release。

## 提交前

- [ ] 确定专用 GitHub repository 及可见性。
- [ ] 配置并验证 GPG 或 SSH commit signing。
- [ ] 从最终 freeze manifest 生成 release allowlist。
- [ ] 扫描绝对路径、密钥、token、邮箱和受限数据。
- [ ] 验证所有 manifest 哈希。
- [ ] 确认 Layer D ROP outcome 不在 staging 区。
- [ ] 负责人确认可执行外部发布。

## Commit 与 release

- [ ] 创建 signed commit。
- [ ] 本地执行签名验证并保存输出。
- [ ] 使用固定 tag，例如 `cross-well-protocol-v1.0-frozen`。
- [ ] release 附加与 OSF 完全相同的冻结 ZIP 和 SHA-256 文本。
- [ ] release notes 写明：协议冻结时间、OSF registration ID、outcome
      当时不可访问、Zenodo 尚未或已经发布。
- [ ] 记录 commit SHA、tag、release URL、release archive SHA-256。

## 当前环境检查结果

- Git 工作区：存在，但项目内容目前基本为 untracked。
- Git remote：未检测到。
- commit signing key / `commit.gpgsign`：未检测到已配置值。

因此 GitHub 证据尚未执行，状态为 `TO_BE_CONFIGURED_BEFORE_V1.0_RELEASE`。

