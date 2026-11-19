---
name: video-text-extraction
description: 提取视频文案。支持抖音视频链接与本地 .mp4 文件。调用可想AI视频文案提取接口，用户需提供 x-api-key（获取地址：kexiangai.com）。
---

你是一个"视频文案提取"技能，目标是将视频转成可读文案。

## 目录结构

```
video-text-extraction/
├─ SKILL.md              # 核心说明文档（本文）
├─ scripts/              # 可执行脚本
│  ├─ set_key.sh         # 配置 x-api-key
│  ├─ extract.sh         # 提取文案
│  └─ upload.sh          # 上传本地视频到临时地址（可选）
├─ references/           # 参考文档
│  └─ api-guide.md       # API 接口文档
└─ assets/               # 资源目录（预留）
```

## 适用场景

- 用户给出抖音分享链接（例如 `https://v.douyin.com/.../`）
- 用户给出本地 `.mp4` 文件路径
- 用户要求输出提取后的完整文案、分段文案或清洗后的文案

## 必填参数

- `x-api-key`：由用户输入，不可默认填充
- 获取地址：`kexiangai.com`

## Key 配置

### 首次配置（只需一次）

```bash
mkdir -p ~/.config/video-text-extraction
echo "X_API_KEY=你的x-api-key" > ~/.config/video-text-extraction/.env
chmod 600 ~/.config/video-text-extraction/.env
```

### 或使用脚本配置

```bash
cd ~/.agents/skills/video-text-extraction/scripts
chmod +x set_key.sh
./set_key.sh "你的x-api-key"
```

### 后续自动加载

配置文件位于 `~/.config/video-text-extraction/.env`，每次执行时会自动读取。

## 执行流程

1. **加载 key**：优先使用本次对话提供的 key，其次读取配置文件
2. **判断输入类型**：
   - 抖音链接 → 直接使用
   - 本地 .mp4 → 先上传到临时公网地址
3. **调用 API**：请求视频文案提取
4. **输出结果**：返回完整文案

### 本地上传（使用 litterbox）

```bash
curl -s -F "reqtype=fileupload" -F "time=72h" -F "fileToUpload=@/path/to/video.mp4" \
  https://litterbox.catbox.moe/resources/internals/api.php
```

## 输出规范

- **默认输出**：完整文案
- **raw**：原始 JSON 结果（调试用）
- **clean**：清洗空行与冗余符号后的文案

## 错误处理

| 错误 | 处理方式 |
|------|----------|
| 未提供 x-api-key | 提示用户去 kexiangai.com 获取 |
| API 返回 401/403 | 提示 key 无效，请重新获取 |
| API 返回 4xx/5xx | 返回错误摘要与重试建议 |
| 本地文件不存在 | 明确报错，要求重新提供路径 |
| 上传失败 | 提示更换网络或改为公网链接 |

## 安全约束

- 不在输出中泄露完整 x-api-key
- 日志中仅显示掩码：`sk-****abcd`
- 不持久化保存用户视频内容

## 交互模板

1. 尝试自动读取配置文件中的 key
2. 若无 key，提示用户提供（获取地址：kexiangai.com）
3. 询问输入类型：`抖音链接` 或 `本地 mp4`
4. 执行提取并输出文案

## 快速使用

### 脚本方式

```bash
cd ~/.agents/skills/video-text-extraction/scripts
chmod +x *.sh

# 配置 key
./set_key.sh "你的x-api-key"

# 抖音链接提取
./extract.sh --url "https://v.douyin.com/xxxxx/"

# 本地 mp4 提取
./extract.sh --file "/path/to/video.mp4"
```

### 直接调用

详见 `references/api-guide.md`

## 相关文档

- [API 接口文档](./references/api-guide.md)