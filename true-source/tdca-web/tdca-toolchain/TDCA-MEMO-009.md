# TDCA-MEMO-009：MOU 计量存证规范（草案）

> **版本：** DRAFT V0.1  
> **编制：** Reasonix 协议编译器（根据 TDCA-FC-20260801-003 代码生成）  
> **制度依据：** ID79（MOU原理）、TDCA-PRINCIPLE-MOU-001、TDCA-MEMO-006、TDCA-MEMO-008  
> **状态：** 待 TDCA 制度委员会审议

---

## 一、目的

本规范定义 MOU（最低可见效用）的计量、记录、存证与验证标准，确保税收锚定的不可伪造性与审计可追溯性。

## 二、核心原则

1. **事实记录原则**：MOU 是配置权交易真实经济价值的不可辩驳硬下限。AI 只能记录/锚定已发生的税收事实，无权"生成"税收数据。
2. **模拟隔离原则**：模拟阶段的 Pre-Est 必须标记 `[SIMULATED]`，不得参与激活系数计算。
3. **Token 锚定原则**：每条 MOU 记录必须引用有效 Config-Right-Token（Token-Ref）。
4. **审计只追加原则**：已归档 MOU 的税收字段不可修改，审计轨迹只追加。

## 三、数据模型

```yaml
MOU-ID: "TDCA-MOU-{YYYYMMDD}-{NNN}"
Token-Ref: "TDCA-CRT-{YYYYMMDD}-{NNN}"    # 必填
NCA-Ref: "TDCA-NCA-{YYYYMMDD}-{NNN}"      # 可选
Recorded-At: "{UTC ISO8601}"
Operator: "string"

Tax-In: null | float                        # 进项税收（真实数据）
Tax-Out: null | float                       # 出项税收（真实数据）
Actual-Total: null | float                  # = Tax-In + Tax-Out

Pre-Est: null | float                       # 预估值（模拟阶段）
Pre-Est-Status: null | "[SIMULATED]"        # 模拟阶段强制标记

Activation-Coefficient: null | float        # (Actual-Total + 就业社保) / 政府PCR
                                            # Actual-Total 为 null 时必须为 null

Granted-By: "TDCA-PRINCIPLE-MOU-001"
Audit-Trail: "string"
```

## 四、验证规则（validate）

| # | 检查项 | 通过条件 |
|---|--------|---------|
| 1 | MOU-ID 格式 | 匹配 `^TDCA-MOU-\d{8}-\d{3}$` |
| 2 | Token-Ref 有效 | 格式合法 + Token 文件存在 |
| 3 | 模拟标记 | Tax-In/Out 均为 null 时，Pre-Est 必须存在且标记 `[SIMULATED]` |
| 4 | 激活系数联动 | Actual-Total 为 null 时，Activation-Coefficient 必须为 null |
| 5 | 时间戳顺序 | Token.created_at < MOU.recorded_at |

## 五、激活系数

```
Activation-Coefficient = (Tax-In + Tax-Out + 就业社保) / 政府初始 PCR 投入

约束：
- gov_pcr > 0（否则 ValueError + [NSFL-TRIGGER]）
- 仅基于 Actual-Total 计算，Pre-Est 不可参与
- 生态沙盒准入阈值：α > 1.2（TDCA 生态沙盒规则）
```

## 六、NSFL 负空间声明

- 禁止伪造税收数据
- 禁止用 Pre-Est 替代 Actual-Total
- 禁止创建无 Token-Ref 的 MOU 记录
- 禁止修改已归档 MOU 税收字段

## 七、与工具链的衔接

```
TDCAConfigRightTokenGenerator → Token-ID
    → TDCANCAGenerator → NCA-ID
        → TDCAMOURecorder → MOU-ID
            → tdca_verify_chain → 三级关联链验证
```

---

> **本草案待审议**：TDCA 制度委员会应评估模拟阶段的 Pre-Est 保留期限、激活系数阈值校准、以及与数字人民币税务系统的对接方案。
