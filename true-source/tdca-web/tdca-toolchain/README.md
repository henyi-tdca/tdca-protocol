# TDCA 工具链（tdca-toolchain）

> **版本：** 1.0.0  
> **制度锚定：** TDCA-MEMO-006, TDCA-MEMO-008, TDCA-PRINCIPLE-MOU-001, ID79  
> **Function-Call-ID：** TDCA-FC-20260801-003

## 一、安装

```bash
pip install pyyaml
cd tdca-toolchain
pip install -e .
```

## 二、环境变量

```bash
export TDCA_TOKEN=TDCA-CRT-20260801-001   # 配置权 Token（必填）
```

Windows PowerShell:

```powershell
$env:TDCA_TOKEN = "TDCA-CRT-20260801-001"
```

## 三、使用

### 3.1 配置权前置声明（token）

```bash
tdca-tool token --type FileMove --path /src/file.go --risk HIGH --signature "HUMAN-SIG"
```

### 3.2 嵌套认知资产记录（nca）

```bash
tdca-tool nca --type CodeGen --path /tmp/code.py --pre-hash <SHA256> --post-hash <SHA256>
```

### 3.3 MOU 计量锚定（mou）

```bash
# 模拟阶段（Pre-Est 标记 [SIMULATED]）
tdca-tool mou --token-ref TDCA-CRT-20260801-001 --pre-est 1000.0

# 实际数据阶段
tdca-tool mou --token-ref TDCA-CRT-20260801-001 --tax-in 500 --tax-out 300 --gov-pcr 400
```

### 3.4 三级关联链验证（verify）

```bash
tdca-tool verify --fc-id TDCA-FC-20260801-003 --output report.yaml
```

## 四、权限模型

- 每次调用前执行 `_check_auth()`：
  - 必须提供 `TDCA_TOKEN` 环境变量或 `--token`
  - `--risk HIGH` 必须提供 `--signature`
- 操作日志写入 `.tdca-nca/cli-audit.log`

## 五、目录结构

```
.tdca-nca/
├── tokens/       # 配置权 Token
├── nca/          # 嵌套认知资产
├── mou/          # MOU 记录
├── cli-audit.log # CLI 操作日志
└── archives/     # 归档
```

## 六、NSFL 约束

- 禁止伪造税收数据（Tax-In/Tax-Out 必须为真实数据源或显式 null）
- 禁止用 Pre-Est 替代 Actual-Total 计算 Activation-Coefficient
- 禁止创建无 Token-Ref 的 MOU 记录
- 禁止修改已归档 MOU 的税收字段（审计轨迹只追加）
