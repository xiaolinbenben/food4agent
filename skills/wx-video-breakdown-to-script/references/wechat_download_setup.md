# Mac 下载微信视频号视频的工具与操作

## 工具：ltaoo/wx_channels_download

GitHub: https://github.com/ltaoo/wx_channels_download

**Mac arm64**（Apple Silicon）直链：
https://github.com/ltaoo/wx_channels_download/releases/download/v260507/wx_video_download_v260507_darwin_arm64.zip

**Mac x86_64**（Intel）：
https://github.com/ltaoo/wx_channels_download/releases/download/v260507/wx_video_download_v260507_darwin_x86_64.zip

> 查看自己 Mac 架构：终端运行 `uname -m`，`arm64` → Apple Silicon，`x86_64` → Intel。

---

## 工作原理（先看懂）

启动后做三件事：
1. 在本机 `127.0.0.1:2023` 跑代理，**自动设为系统代理**（拦截微信流量）
2. 在 `127.0.0.1:2022` 跑管理 API
3. 默认下载目录 = `~/Downloads/`

它不是嗅探+另存，而是**往微信视频播放器里注入一个"下载"按钮**。

---

## 安装与启动

```bash
# 1. 下载并解压（zip 自动放到 ~/Downloads/）
# 解压后路径示例：~/Downloads/wx_video_download_v260507_darwin_arm64/

# 2. 解掉 macOS Gatekeeper 隔离（首次必须）
xattr -dr com.apple.quarantine ~/Downloads/wx_video_download_v260507_darwin_arm64

# 3. 以管理员身份启动（要装本地根证书）
cd ~/Downloads/wx_video_download_v260507_darwin_arm64
sudo ./wx_video_download
```

第一次启动会弹钥匙串密码框（装根证书）。终端看到「代理服务启动成功」就行。

---

## 操作步骤

### 1. 确认服务起来了

```bash
curl http://127.0.0.1:2022/ping
```

### 2. 打开 Mac 微信客户端
- **不要用网页版**，要用桌面微信
- 进入"视频号"或者打开别人转发的视频号链接
- 找到对标账号，点开任意一条视频

### 3. 下载视频
- 视频开始播放后**暂停**
- 播放器右上角/工具栏会出现一个**"下载"按钮**（工具注入的）
- 点下载，会弹出清晰度选择
- 下载完文件出现在 `~/Downloads/` 根目录，文件名是视频标题+清晰度

### 4. 整理到对标目录

```bash
mkdir -p ~/Downloads/对标账号
mv ~/Downloads/*视频标题关键字*.mp4 ~/Downloads/对标账号/
```

### 5. 退出工具

在跑工具的终端 `Ctrl+C`。**一定要正常退出**，否则系统代理还留着，其他网站可能上不去。

---

## 常见问题

| 现象 | 原因 / 解决 |
|---|---|
| 微信里看不到"下载"按钮 | 退出并重启微信客户端（让它重新走代理） |
| 浏览器/其他 app 上不了网 | 工具没正常退出。系统设置 → 网络 → Wi-Fi → 详细信息 → 代理，手动关 HTTP/HTTPS 代理 |
| 弹"证书不受信任" | 钥匙串访问搜 `wx_channels` 或 `mitm`，双击 → 信任 → 始终信任 |
| 用了 xray/clash | 临时关掉，否则代理链冲突 |
| 下载按钮点了无反应 | 看跑工具的终端输出，多半是没拿到 feed，刷新视频页重试 |
| `command not found: ./wx_video_download` | 没 cd 到解压后的目录就执行了 |

---

## 替代方案

如果用户不在 Mac，或对 wx_channels_download 不放心：
- **抖音/小红书**：直接用浏览器开发者工具 Network 面板抓 mp4
- **直接录屏**：QuickTime Player 录屏 → 后期裁剪。质量略损但合规风险最低
- **找 KOL 要原片**：如果对方愿意分享，是最干净的方式

> ⚠️ 拉片仅用于内部学习和复盘自家选题方向，不要做二次发布。
