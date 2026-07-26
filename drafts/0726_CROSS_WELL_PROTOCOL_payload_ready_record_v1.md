# CROSS-WELL 协议载荷就绪记录

- 状态：`PAYLOAD_READY_PENDING_EXTERNAL_TIMESTAMP_AND_UNLOCK_GATE`
- 协议目录：`drafts/0724_CROSS_WELL_PROTOCOL_v0.9-draft_v1`
- 候选 ZIP：`drafts/0726_CROSS_WELL_PROTOCOL_v0.9-draft_payload-ready_v1.zip`
- ZIP SHA-256：`B541B5E75E129472980EF848C95DB7299CB4EFAC3E5EFEC7ACD2F32AE68B18A1`
- ZIP 大小：`3,485,929 bytes`
- `16_freeze_manifest.json` SHA-256：`AF25648E8BCA8762B3209F1447F462E6DE2B119CB6F09A1AC74A5183D6BBF6F8`
- Manifest 覆盖文件：`138`
- 冻结评分来源映射：`23` 个 qualified families
- 严格校验：`PASS`
- 未决科学/执行占位符：`0`
- Layer D 数值 ROP：`未访问`

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
