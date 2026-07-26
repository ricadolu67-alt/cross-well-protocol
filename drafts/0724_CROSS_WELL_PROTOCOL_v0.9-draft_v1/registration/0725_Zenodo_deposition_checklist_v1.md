# Zenodo final reproduction package checklist

Zenodo 用于研究完成后的最终公开复现包 DOI，不替代 outcome unlock 前的 OSF
Registration。当前阶段只准备元数据和交付规则，不创建 deposition。

## 最终包至少包含

- [ ] OSF Registration ID/DOI 与注册时间。
- [ ] GitHub signed commit、release tag 和验证记录。
- [ ] `CROSS_WELL_PROTOCOL_v1.0-frozen` 原始包。
- [ ] v1.0 SHA-256 manifest 与 archive digest。
- [ ] 单次冻结执行的 stdout、stderr 和 execution trace。
- [ ] 全部预定义结果表，包括不利或零结果。
- [ ] protocol deviation log、原始分析和必要的 corrected full-cohort rerun。
- [ ] 可公开的代码、环境锁、模型工件和数据来源说明。
- [ ] Data Availability 与受限原始数据的获取说明。
- [ ] 明确的软件和数据许可证。

## 建议元数据

- Title: `CROSS-WELL confirmatory protocol and reproducibility package for
  cross-field ROP transport`
- Resource type: Dataset or Software（根据最终包的主要内容在投稿前确定）
- Creators / affiliations / ORCID: `Lu Yuhan (陆宇晗); Changzhou University; https://orcid.org/0009-0006-8513-2732`
- Description: `DERIVE_FROM_FINAL_ACCEPTED_ABSTRACT_AFTER_CONFIRMATORY_EXECUTION`
- Related identifiers: OSF Registration、GitHub release、论文 DOI
- Version: `1.0` 或最终复现包版本
- License: `SELECT_ONLY_AFTER_FINAL_RIGHTS_AND_DATA-REUSE_AUDIT`
- Keywords: ROP; cross-well generalization; external validation; measurement
  semantics; confirmatory protocol

## 发布门槛

只有在确认性执行完成、隐私/许可审计完成、所有结果均保留且负责人再次明确批准
后才可发布。
