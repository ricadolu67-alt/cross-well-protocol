# CROSS-WELL 协议载荷就绪记录

- 状态：`PAYLOAD_READY_PENDING_EXTERNAL_TIMESTAMP_AND_UNLOCK_GATE`
- 协议目录：`drafts/0724_CROSS_WELL_PROTOCOL_v0.9-draft_v1`
- 候选 ZIP：`drafts/0726_CROSS_WELL_PROTOCOL_v0.9-draft_payload-ready_v2.zip`
- ZIP SHA-256：`4775B236C2E9C296FA27CFD82FBA3B359AD6725872F806845467C31008FCBE54`
- ZIP 大小：`3,488,234 bytes`
- `16_freeze_manifest.json` SHA-256：`6C521FF9917A56F0E7C076DC57567CAF35B74DE81D0E2B224EA8C1BCB6E5436D`
- Manifest 覆盖文件：`139`
- 冻结评分来源映射：`23` 个 qualified families
- 严格校验：`PASS`
- 未决科学/执行占位符：`0`
- Layer D 数值 ROP：`未访问`
- 公开载荷中的本机绝对归档路径：`0`

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
