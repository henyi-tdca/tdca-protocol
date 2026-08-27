# IDENTITY · 智能体身份绑定声明

> 用途：让我的智能体代表我参与 TDCA 协作（组建/加入联盟、缔约、贡献 COP）。
> 流程：本地生成密钥 → 填写本文件 → PR 到本仓库 → enforce_entry 校验 → 获得发射权。

## 一、声明
- 我（GitHub 用户名）：tdca-mvp-demo-user
- 声明以下智能体代表我参与 TDCA 协作：
  - 智能体标识：wb-v01-agent
  - 公钥指纹：256 SHA256:+GHiqFTYse+QsnxBnKsNECNzP4QwmAgf/D57C9wPJvk tdca-mvp-demo-user-tdca-agent (ED25519)
- 生成时间：2026-08-27T14:32:19.520922+00:00
- 用途声明：代表我组建科研协作联盟并贡献思维协议 COP

## 二、校验与确权
- enforce_entry 扫描校验：公钥指纹格式 + 声明字段完整性（自动）
- 通过 = 轻量身份绑定（我的智能体获得发射权）
- 制度确权（另行）：参与缔约时生成 OPC 准入 NCA（缔约者自签署）

## 三、纪律
- 私钥永不上传（仅公钥指纹入仓；本测试私钥存于系统 TEMP，生成后即删，零落盘）
- 一个 GitHub 用户可绑定多个智能体（各自独立指纹）
