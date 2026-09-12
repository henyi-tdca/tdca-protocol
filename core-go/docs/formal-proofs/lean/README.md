# Lean 4 形式化证明工程骨架

本目录承载 TDCA 白皮书中数学命题的 Lean 4 形式化候选件。

## 状态声明（重要）

- 入库文件均为 **CANDIDATE（候选）** 状态：须通过 CI 机验（`lake env lean` 零错误）方为机验通过。
- **机验通过不等于 Tier A**：升档须另行完成签批流程，且要求 `sorry` 计数为零。
- 当前候选件 `TDCA/ExPostTrust.lean` 版本为 **V1.2**：`sorry` 已**清零**
  （`corollary2_effort_comparative_statics` 已由初等单调性路径全证，纯实数序公理、
  无分析库依赖）；升档（Tier A）已由签批流程裁定。
  CI 闸门固定校验 `sorry` 计数 = **0**（加严后），防止静默回退。

## 目录结构

```
lean/
├── lean-toolchain          # 固定 Lean 工具链版本
├── lakefile.toml           # Lake 工程定义（依赖 Mathlib）
├── README.md               # 本文件
└── TDCA/
    └── ExPostTrust.lean    # 候选件（内容锁定，改动须另立版本）
```

## 本地验证（可选）

需安装 [elan](https://github.com/leanprover/elan)。首次运行会自动按
`lean-toolchain` 拉取对应工具链：

```bash
cd core-go/docs/formal-proofs/lean
lake exe cache get   # 拉取 Mathlib 预编译缓存，避免全量编译
lake env lean TDCA/ExPostTrust.lean
```

预期结果：退出码 0（零 error），无 `sorry` 警告。
