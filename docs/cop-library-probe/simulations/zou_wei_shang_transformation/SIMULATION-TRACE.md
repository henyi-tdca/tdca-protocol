# 走为上计 · 思维协议调度模拟轨迹

时间: 2026-08-14T17:37:37.566122

- **[LOAD]** 加载顶层控制器 STRATAGEM-COP-20260814-36 (走为上/败战计)
- **[LOAD]** 加载被调度 skill 源 MCKINSEY-COP-20260813-001 (麦肯锡管理咨询顾问)
- **[GATE]** 决策门[必败不可战?] 信号={'毛利转负': True, '份额不可逆下滑': True, '技术替代不可逆': True, '中标率低于盈利门槛': True} -> 结论=TRUE 调度
- **[DISPATCH]** 触发原语 zou_wei_shang (走为上) | 签名 fn zou_wei_shang(context: Situation) -> Outcome
- **[DISPATCH]** 负空间 ⊗ ⊗ 可战而走则失机; 非怯战是知止
- **[STEP1]** 识不可为: 固化必败证据链
- **[STEP2]** 全师而退: 设计有序退出
- **[STEP3]** 保根本待机: 向下调度麦肯锡规划原语生成转型方案
- **[SKILL]** SkillCall mece_decompose -> 3 互斥子集: 识不可为 (确认必败)/全师而退 (有序退出)/保根本 (核心资产封存)
- **[SKILL]** SkillCall seven_step_solve -> 7 步方案, 主线=seven_step_solve
- **[SKILL]** SkillCall scp_frame -> 叙事定调完成

## 决策门信号快照

- legacy_gross_margin: -6.2% (连续 5 季为负)
- legacy_market_share_yoy: -19.4%
- win_rate_new_bid: 11% (行业可盈利门槛约 35%)
- tech_substitution: 不可逆 (电动化已成本曲线交叉)
- cash_burn: 该产品线年净现金流出 ¥2.1 亿

## 校验

- 走为上 COP 验证: {'passed': True, 'issues': [], 'primitive_count': 1}
- 麦肯锡 COP 验证: {'passed': True, 'issues': [], 'primitive_count': 7}
- 负空间: ['⊗ 可战而走则失机; 非怯战是知止', '⊗ 禁止机械套用: 计须契合态势, 非态势则不用', '⊗ 禁止违反 NSFL: 伦理/法律负空间不可越']