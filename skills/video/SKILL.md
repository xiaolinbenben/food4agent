---
name: video
description: 视频脚本 / 分镜 / 视频生成。
when-to-use: 用户要做视频脚本 / 分镜表 / 短视频 / 视频生成时
allowed-tools: generate_video, Read, Write
---

# 视频

你被激活来交付视频相关产物。

## 交付路径

- **视频脚本 / 分镜** → 完整分镜表（时间码 / 画面描述 / 旁白 / 转场）输出为 markdown，落到文件。
- **真实视频生成** → 若 `generate_video`（hosted video tool）可用则调用生成；不可用就如实告诉用户、
  降级为脚本 + 关键帧图像（image_generation）。**不要假装生成了视频**——没生成就说没生成（不掩盖问题）。

进度反馈：动手前一句话说清你要做什么。
