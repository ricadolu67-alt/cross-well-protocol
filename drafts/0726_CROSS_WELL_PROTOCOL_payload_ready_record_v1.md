# CROSS-WELL 协议载荷就绪记录

- 状态：`PAYLOAD_READY_PENDING_EXTERNAL_TIMESTAMP_AND_UNLOCK_GATE`
- 协议目录：`drafts/0724_CROSS_WELL_PROTOCOL_v0.9-draft_v1`
- 候选 ZIP：`drafts/0726_CROSS_WELL_PROTOCOL_v0.9-draft_payload-ready_v3.zip`
- ZIP SHA-256：`7B972411D28A1F59BF67FEA2C5BEAACCE2EC1C7010A3A55CB96C53DCFB7FB6B8`
- ZIP 大小：`3,488,216 bytes`
- `16_freeze_manifest.json` SHA-256：`7866E0768C5D93DF535C8EE9E3EB2B026C3913CCD0780A1415FD8C3DF88C1869`
- Manifest 覆盖文件：`139`
- 冻结评分来源映射：`23` 个 qualified families
- 严格校验：`PASS`
- 未决科学/执行占位符：`0`
- Layer D 数值 ROP：`未访问`
- 公开载荷中的本机绝对归档路径：`0`
- 私有本地归档定位 sidecar：`drafts/0726_CROSS_WELL_private_execution_sidecars_v1/0726_local_archive_locator_completed_v1.json`
- 私有定位 sidecar SHA-256：`F4D16D19F72674C8295E4B9149C1E50A244A7E4FBC5E19C6531D8F3609F1CD77`
- 已整文件复核的评分归档：`23 / 23`

## 非循环外部门

载荷内 F01--F22 已通过。F23（可信时间戳）和 F24（解锁前 outcome
仍不可访问）保留为 `EXTERNAL_GATE_PENDING`。这两项必须在载荷 ZIP
固定之后由外部 sidecar 证明，不能回写进已时间戳的载荷。

固定执行命令为：

```text
python scripts/execute_frozen_run.py
```

该命令在以下证据全部进入
`registration_external/0726_external_unlock_gate_completed_v1.json` 前会
fail closed：OSF Registration、GitHub signed immutable release、解锁前 custody
重确认以及 Lu Yuhan 的单次书面授权。

本记录不是 outcome unlock 授权，也不是 OSF Registration 回执。
