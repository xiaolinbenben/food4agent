# 微信视频号对标拉片 → 脚本批量生成 · Claude Code Skill

> 把"对标账号视频 → 拉片 → 提炼公式 → 批量脚本 → 带图 Word"完整自动化的工作流，
> 封装成一个可分享的 Claude Code skill。

---

## 这个 skill 解决什么问题

短视频赛道做内容矩阵，最大的瓶颈是「**对着对标账号写脚本**」这一步——
- 拉片要看几十条视频，每条都要逐镜拆解
- 提炼公式要做横向对比
- 批量生成脚本要重复写 6 个模块
- 给团队的执行文档要带图、要排版

这个 skill 让 Claude 把这一整套都跑下来。**输入**：一个对标视频文件夹。**输出**：拉片报告 + 4 套骨架模板 + 选题库 + 批量脚本 + 带图 Word。

---

## 安装到你的 Claude Code

### 方式 A：直接复制（推荐，最简单）

```bash
# 1. 把这个文件夹复制到你的全局 skills 目录
cp -r ./_share_skill_video_breakdown ~/.claude/skills/wx-video-breakdown-to-script

# 2. 验证
ls ~/.claude/skills/wx-video-breakdown-to-script/
# 应该看到: SKILL.md, scripts/, references/, templates/
```

下次 Claude Code 启动时这个 skill 就被加载了。

### 方式 B：项目级 skill（只对某个项目可见）

```bash
# 在你的项目根目录
mkdir -p .claude/skills
cp -r /path/to/_share_skill_video_breakdown .claude/skills/wx-video-breakdown-to-script
```

---

## 前置依赖

| 工具 | 用途 | 安装方式 |
|---|---|---|
| **Mac** | 微信视频号下载工具只有 macOS 和 Windows 版 | — |
| **Python 3.8+** | 抽视频关键帧 | 系统自带 / `brew install python` |
| **opencv-python** | cv2 抽帧 | `pip install opencv-python` |
| **Node.js 18+** | 生成 Word 文档 | `brew install node` |
| **docx package** | Node.js 的 Word 生成库 | `npm install -g docx` |
| **wx_channels_download** | 下载视频号视频（可选） | [GitHub releases](https://github.com/ltaoo/wx_channels_download/releases) |

---

## 用法（同事拿到后怎么用）

### 1. 下载几条对标视频
用 `wx_channels_download` 下载 3-5 条对标账号的视频到一个目录。详细操作步骤在 `references/wechat_download_setup.md`。

### 2. 打开 Claude Code，自然语言对话

```
我下载了一些综评对标账号的视频在 ~/Downloads/对标账号/ 里，
帮我拉片，然后生成 10 条照葫芦画瓢的脚本。
```

Claude 会自动触发这个 skill，按流程走：
- Step 1 列出视频，让你挑要精拉的几条
- Step 2 抽帧 → 看图 → 写拉片报告
- Step 3 提炼公式 → 写分镜模板 + 选题库
- Step 4 批量生成脚本
- Step 5（可选）导出带图 Word

### 3. 后续可以继续问

```
帮我把 11 号脚本升级成详细版本
给 BNBU 系列做带图 Word 合集
新增 10 条选题，按相同格式批量生成
```

---

## 文件结构

```
_share_skill_video_breakdown/
├── SKILL.md                          ← Claude 读的入口（关键）
├── README.md                         ← 你正在看的这个文件
├── scripts/
│   ├── extract_frames.py             ← cv2 抽帧脚本
│   └── build_word.js                 ← Word 生成器模板
├── references/                       ← 工作流细节文档
│   ├── wechat_download_setup.md      ← Mac 下载视频号视频的步骤
│   ├── breakdown_method.md           ← 拉片 5 大维度 + 抽帧策略
│   ├── skeleton_taxonomy.md          ← 4 套骨架定义 + 字幕色规
│   └── script_format_spec.md         ← 单条脚本的 6 模块规范
└── templates/
    ├── topics.csv                    ← 选题库模板（含示例行）
    └── script_template.md            ← 单条脚本骨架
```

---

## 适用场景

✅ 完美适用：
- 综评/升学规划赛道（实测过）
- 财经/教育/法律等口播垂类
- 30-180 秒的竖屏短视频
- 视频号 + 抖音 + 小红书 + 公众号四端联动

⚠️ 不太适合：
- 纯剧情短剧（没有"骨架"概念）
- 长视频 / 直播切片
- 完全原创、没对标的内容

---

## FAQ

**Q：抽帧 + 看图能 100% 还原对标视频内容吗？**
A：约 80%。字幕和口播 95% 同步的口播视频可以靠抽帧 + 看字幕还原。如果对方做的是真人对话采访（无字幕），需要额外用 whisper 转录。

**Q：生成的脚本数据是真的吗？**
A：**不是**。涉及具体政策/数字（如某校招生人数）的内容，skill 会**留占位符**并提醒你去对官方简章。这个 skill 的价值是把"内容结构"复刻，**不是凭空编造数据**。

**Q：能不能不导出 Word，只要 Markdown？**
A：可以。告诉 Claude "不需要 Word，只要 .md" 就行。

**Q：脚本里的发布文案不用我自己改吗？**
A：可以微调，但 skill 已经按平台特性写好了：视频号/抖音短文案、小红书带 emoji 长文案、公众号导流文案。

**Q：能扩展到别的院校 / 别的赛道吗？**
A：完全可以。`references/skeleton_taxonomy.md` 里 4 套骨架是通用的，把"对标账号"和"目标人群"换成你的赛道就行。

---

## 制作信息

- 出品：择枢综评短视频项目组（基于真实生产场景沉淀）
- 数据来源：升途教育/飞学长公众号近 100 条视频的拉片分析
- 维护：项目主理人 + Claude Code（迭代中）

如果你的赛道用这个 skill 跑通了，欢迎反馈，会持续迭代。
