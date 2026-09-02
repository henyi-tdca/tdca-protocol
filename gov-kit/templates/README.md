# 研发治理包模板索引（templates/）

> K1-3 模板独立化｜ 12 份机器可读模板，yaml 全部可解析（校验 PASS 12/12）
> 使用：复制模板填写，必填字段标注 [R]；record_ref 通用存证号字段

| 模板 | 对应制度 | 主键 |
|---|---|---|
| gk-01-trial.yaml | GK-01 试验门 | trial_id |
| gk-02-canary.yaml | GK-02 灰度门 | canary_id |
| gk-03-reliability.yaml | GK-03 可靠性检查单 | reliability_check |
| gk-04-settlement.yaml | GK-04 统一结算 | settlement |
| gk-05-mouzero.yaml | GK-05 效用归零 | mouzero |
| gk-06-fastslow.yaml | GK-06 快慢双层 | fastslow |
| gk-07-ops.yaml | GK-07 运维分级 | ops_entry |
| gk-08-weekly.yaml | GK-08 优化周快照 | weekly_snapshot |
| gk-09-innovation.yaml | GK-09 创新双通道 | innovation_id |
| gk-10-stack.yaml | GK-10 零自研对接 | stack_item |
| gk-11-orch.yaml | GK-11 编排闭环 | orch_task |
| gk-12-gatechain.yaml | GK-12 三重门全链 | gate_chain |
