/**
 * 视频脚本系列 Word 生成器（带示意图）
 *
 * 用法：
 *   1. 把这个文件复制到你的工作目录（例如 06_脚本批次/build_word.js）
 *   2. 修改下方 CONFIG 区配置（IMG_DIR、TITLE、OUT_NAME）
 *   3. 修改 SCRIPTS 数组，每个对象一条脚本
 *   4. 运行：NODE_PATH=~/.npm-global/lib/node_modules node build_word.js
 *
 * 前置：npm install -g docx
 *
 * 字幕色规（贯穿整份文档）：
 *   黄字 #E89B1A = 数字
 *   红字 #C00000 = 结论
 *   白字 #FFFFFF = 旁白
 *   品牌红 #D33A2C = 标题板红框
 */

const fs = require('fs');
const path = require('path');
const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell, ImageRun,
  AlignmentType, LevelFormat, HeadingLevel, BorderStyle, WidthType, ShadingType,
  PageBreak, VerticalAlign,
} = require('docx');

// ========================= CONFIG =========================
// 改这里：你的关键帧目录（运行 extract_frames.py 输出的目录）
const IMG_DIR = path.join(__dirname, '..', '01_拉片报告', '拉片关键帧');

// 改这里：合集标题
const COVER = {
  title: 'XX 2026 系列短视频脚本合集',
  subtitle: '1 总览 + N 专题',
  brand: '择枢综评短视频项目组',
  version: 'v1.0 · 2026-MM-DD',
};

// 改这里：输出文件名
const OUT_NAME = 'XX2026系列脚本合集.docx';

// 改这里：固定标签包（9 个，顺序不变）
const FIXED_TAGS = '#东莞综评 #东莞多元升学 #广东综合评价 #广东综评院校 #综合评价招生政策 #广东综合评价面试技巧 #华南理工大学综评 #中山大学综评 #香港中文大学深圳';

// 改这里：要展示的样式参考图（从 IMG_DIR 找）
// 如果没有可用图，把这一段的 REFERENCE_FRAMES 设为 null
const REFERENCE_FRAMES = {
  brandStyle: [
    { file: 'brand_logo.jpg',       caption: '① 顶部红框标题板（常驻全片）' },
    { file: 'brand_yellow.jpg',     caption: '② 中央黄字大数（数字必黄）' },
    { file: 'brand_redformula.jpg', caption: '③ 黄+红组合公式' },
  ],
  shootScene: [
    { file: 'B_hook.jpg',      caption: '机位 A · 图书馆前广场' },
    { file: 'B_titlebar.jpg',  caption: '机位 B · 校园长凳' },
    { file: 'B_interview.jpg', caption: '机位 C · 主教学楼前' },
  ],
};

// ========================= SCRIPTS =========================
// 改这里：每条脚本一个对象
// 字段含义见 references/script_format_spec.md
const SCRIPTS = [
  {
    num: '01',
    title: '示例脚本：钩子句要让人停下来',
    skeleton: 'A 干货拆解',
    cast: '飞学长 1 人',
    duration: '80 秒',
    diff: '⭐⭐',
    tagline: '一句话讲清楚本片的核心价值——这里是钩子+承诺。',
    shootPrep: [
      ['场地', 'XX 校区 XX 广场 + XX 长凳'],
      ['服装', '白衬衫 + 卡其裤'],
      ['道具', 'A4 纸手写 "100" 做特写'],
      ['同期 B-roll', '校牌特写、航拍、学生剪影'],
      ['拍摄时长', '约 1.5 小时'],
    ],
    vo: [
      ['【0-3s · 钩子】', '钩子句——直接讲核心承诺。'],
      ['【3-15s · 数据铺垫】', '用一组数据建立焦虑/兴趣。'],
      ['【15-35s · 核心点 ①】', '展开第一个核心信息。'],
      ['【35-55s · 核心点 ②】', '展开第二个核心信息。'],
      ['【55-75s · 服务/方法引导】', '自然带出能提供的价值。'],
      ['【75-80s · CTA 收尾】', '评论区留 "XX" 我私发详情。'],
    ],
    storyboard: [
      ['00:00-00:03', '真人@XX 中景', '钩子句', '顶部红框「XX 标题板」+ 副标「XX」+ 底部黄字「XX」'],
      ['00:03-00:15', 'XX B-roll', '数据铺垫', '中央黄字「XX」+ 红字小「XX」'],
      ['00:15-00:35', '真人@XX', '核心点①', '红字大「① XX」+ 黄字「XX」+ 白字「XX」'],
      ['00:35-00:55', '真人@XX', '核心点②', '红字大「② XX」+ 黄字「XX」+ 白字「XX」'],
      ['00:55-01:15', '真人 + B-roll', '服务引导', '白字 3 条列表'],
      ['01:15-01:20', '真人定格', 'CTA', '红字大金句「XX」+ 黄字「评论区留 XX」'],
    ],
    publish: {
      douyin: '简短钩子 + 核心信息 + CTA（≤110 字）',
      xhs: `小红书风格的长文案✨

🎯 三段式
1️⃣ 引出问题
2️⃣ 给出答案
3️⃣ 留 CTA

留言"XX"私发📄`,
      gzh: `公众号完整文章版（可选）`,
    },
    afterCheck: [
      '数字字幕全黄',
      '"调整①②③" 红字大号一致',
      '顶部标题板全程不消失',
      '时长 75-85 秒',
      '私信关键词配置：发 "XX" PDF',
      '9 个固定标签按顺序粘贴',
    ],
    xhsExtraTags: '#XX #XX #XX #XX',
  },
  // 继续追加更多脚本对象...
];

// ========================= 以下不用改 =========================
const FONT = 'Microsoft YaHei';
const PAGE_W = 11906, PAGE_H = 16838, MARGIN = 1080;
const CONTENT_W = PAGE_W - MARGIN * 2;

const C = {
  red: 'C00000', yellow: 'E89B1A', brandRed: 'D33A2C', gray: '595959',
  lightBlue: 'D9E2F3', lightYellow: 'FFF2CC', lightRed: 'FBE5D6', lightGreen: 'E2EFDA',
  border: 'BFBFBF',
};
const border = { style: BorderStyle.SINGLE, size: 4, color: C.border };
const borders = { top: border, bottom: border, left: border, right: border };

function P(text, opts = {}) {
  const { bold, size = 22, color = '000000', align, spacing, italic } = opts;
  return new Paragraph({ alignment: align, spacing: spacing || { after: 80 },
    children: [new TextRun({ text, bold, italics: italic, size, color, font: FONT })] });
}
function H1(text, color = C.brandRed) {
  return new Paragraph({ heading: HeadingLevel.HEADING_1, spacing: { before: 360, after: 200 },
    children: [new TextRun({ text, bold: true, size: 36, color, font: FONT })] });
}
function H2(text) {
  return new Paragraph({ heading: HeadingLevel.HEADING_2, spacing: { before: 280, after: 140 },
    children: [new TextRun({ text, bold: true, size: 28, font: FONT })] });
}
function H3(text) {
  return new Paragraph({ heading: HeadingLevel.HEADING_3, spacing: { before: 180, after: 100 },
    children: [new TextRun({ text, bold: true, size: 24, color: C.gray, font: FONT })] });
}
function Bullet(text) {
  return new Paragraph({ numbering: { reference: 'bullets', level: 0 }, spacing: { after: 60 },
    children: [new TextRun({ text, size: 22, font: FONT })] });
}
function Quote(text, bg = C.lightYellow) {
  const paras = String(text).split('\n').map(line =>
    new Paragraph({ children: [new TextRun({ text: line, size: 22, font: FONT })] }));
  return new Table({ width: { size: CONTENT_W, type: WidthType.DXA },
    columnWidths: [CONTENT_W],
    rows: [new TableRow({ children: [new TableCell({
      borders, width: { size: CONTENT_W, type: WidthType.DXA },
      shading: { fill: bg, type: ShadingType.CLEAR },
      margins: { top: 160, bottom: 160, left: 240, right: 240 },
      children: paras,
    })] })] });
}
function Spacer() { return new Paragraph({ spacing: { after: 100 }, children: [new TextRun('')] }); }
function BR() { return new Paragraph({ children: [new PageBreak()] }); }

function img(filename, w, h) {
  const fullpath = path.join(IMG_DIR, filename);
  if (!fs.existsSync(fullpath)) {
    console.warn(`⚠️  图片不存在: ${fullpath}`);
    return null;
  }
  return new ImageRun({ type: 'jpg', data: fs.readFileSync(fullpath),
    transformation: { width: w, height: h },
    altText: { title: filename, description: filename, name: filename } });
}
function frameRow(frames, frameW = 140, frameH = 249) {
  const valid = frames.filter(f => fs.existsSync(path.join(IMG_DIR, f.file)));
  if (valid.length === 0) return P('（参考图未提供）', { italic: true, color: C.gray });
  const cells = valid.map(f => new TableCell({
    borders, width: { size: Math.floor(CONTENT_W / valid.length), type: WidthType.DXA },
    margins: { top: 100, bottom: 80, left: 80, right: 80 }, verticalAlign: VerticalAlign.TOP,
    children: [
      new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 80 },
        children: [img(f.file, frameW, frameH)] }),
      new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 0 },
        children: [new TextRun({ text: f.caption, size: 18, color: C.gray, italics: true, font: FONT })] }),
    ],
  }));
  const colW = Math.floor(CONTENT_W / valid.length);
  const colWidths = Array(valid.length).fill(colW);
  colWidths[colWidths.length - 1] = CONTENT_W - colW * (valid.length - 1);
  return new Table({ width: { size: CONTENT_W, type: WidthType.DXA }, columnWidths: colWidths,
    rows: [new TableRow({ children: cells })] });
}
function buildTable(headers, rows, opts = {}) {
  let colW = opts.colWidths || Array(headers.length).fill(Math.floor(CONTENT_W / headers.length));
  colW = [...colW];
  colW[colW.length - 1] = CONTENT_W - colW.slice(0, -1).reduce((a, b) => a + b, 0);
  const headerRow = new TableRow({ tableHeader: true,
    children: headers.map((h, i) => new TableCell({
      borders, width: { size: colW[i], type: WidthType.DXA },
      shading: { fill: opts.headerFill || C.brandRed, type: ShadingType.CLEAR },
      margins: { top: 80, bottom: 80, left: 100, right: 100 },
      children: [new Paragraph({ alignment: AlignmentType.CENTER,
        children: [new TextRun({ text: h, bold: true, color: 'FFFFFF', size: 22, font: FONT })] })],
    })),
  });
  const dataRows = rows.map(r => new TableRow({
    children: r.map((cell, i) => new TableCell({
      borders, width: { size: colW[i], type: WidthType.DXA },
      margins: { top: 80, bottom: 80, left: 100, right: 100 }, verticalAlign: VerticalAlign.TOP,
      children: (Array.isArray(cell) ? cell : [cell]).map(line =>
        new Paragraph({ children: [new TextRun({ text: line, size: 20, font: FONT })] })),
    })),
  }));
  return new Table({ width: { size: CONTENT_W, type: WidthType.DXA }, columnWidths: colW, rows: [headerRow, ...dataRows] });
}

function renderScript(data, children) {
  children.push(BR());
  children.push(H1(`${data.num} · ${data.title}`));
  children.push(P(`骨架 ${data.skeleton} · 出镜 ${data.cast} · 目标时长 ${data.duration} · 拍摄难度 ${data.diff}`,
    { color: C.gray, italic: true }));
  children.push(Spacer());

  children.push(H2('🎯 一句话定位'));
  children.push(Quote(data.tagline, C.lightRed));
  children.push(Spacer());

  children.push(H2('🎬 拍摄准备'));
  children.push(buildTable(['项目', '要求'], data.shootPrep, { colWidths: [1800, 7946] }));
  children.push(Spacer());

  children.push(H2('🎤 完整逐字稿'));
  data.vo.forEach(([head, text]) => {
    children.push(new Paragraph({ spacing: { before: 120, after: 60 },
      children: [new TextRun({ text: head, bold: true, size: 22, color: C.brandRed, font: FONT })] }));
    children.push(Quote(text));
  });
  children.push(Spacer());

  children.push(H2('🎞️ 分镜表'));
  children.push(buildTable(['时间', '画面', '口播', '字幕'], data.storyboard,
    { colWidths: [1300, 2200, 2900, 3346] }));
  children.push(Spacer());

  children.push(H2('📱 发布文案'));
  if (data.publish.douyin) { children.push(H3('视频号 / 抖音版')); children.push(Quote(data.publish.douyin, C.lightBlue)); }
  if (data.publish.xhs)    { children.push(H3('小红书版'));    children.push(Quote(data.publish.xhs,    C.lightGreen)); }
  if (data.publish.gzh)    { children.push(H3('公众号导流版')); children.push(Quote(data.publish.gzh,    C.lightYellow)); }
  children.push(Spacer());

  children.push(H2('✅ 后期自检'));
  data.afterCheck.forEach(c => children.push(Bullet(c)));
  children.push(Spacer());

  children.push(H2('🏷️ 标签'));
  children.push(Quote(FIXED_TAGS));
  if (data.xhsExtraTags) {
    children.push(Spacer());
    children.push(P('小红书额外加：', { italic: true, color: C.gray }));
    children.push(Quote(data.xhsExtraTags));
  }
}

// ========================= 文档组装 =========================
const children = [];

// 封面
children.push(new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 2000, after: 200 },
  children: [new TextRun({ text: COVER.title, bold: true, size: 56, color: C.brandRed, font: FONT })] }));
children.push(new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 200 },
  children: [new TextRun({ text: COVER.subtitle, size: 28, font: FONT })] }));
children.push(new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 1200 },
  children: [new TextRun({ text: '出品：' + COVER.brand, size: 22, color: C.gray, font: FONT })] }));
children.push(new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 0 },
  children: [new TextRun({ text: COVER.version, size: 22, color: C.gray, font: FONT })] }));
children.push(BR());

// 系列总览
children.push(H1('📋 系列总览'));
children.push(P(`本合集共 ${SCRIPTS.length} 条脚本。每条都遵循"数字必黄、结论必红、其他必白"的字幕色规。`));
children.push(Spacer());
children.push(buildTable(
  ['编号', '骨架', '标题', '时长', '出镜', '难度'],
  SCRIPTS.map(s => [s.num, s.skeleton, s.title, s.duration, s.cast, s.diff]),
  { colWidths: [700, 1500, 3700, 1100, 1500, 1246] },
));
children.push(Spacer());

// 样式参考
if (REFERENCE_FRAMES && REFERENCE_FRAMES.brandStyle) {
  children.push(H2('🎨 字幕样式参考（剪辑必看）'));
  children.push(P('全部按"数字必黄、结论必红、其他必白"配色：'));
  children.push(Spacer());
  children.push(frameRow(REFERENCE_FRAMES.brandStyle));
  children.push(Spacer());
}

// 场地参考
if (REFERENCE_FRAMES && REFERENCE_FRAMES.shootScene) {
  children.push(H2('📍 场地参考（拍摄师按图选位）'));
  children.push(Spacer());
  children.push(frameRow(REFERENCE_FRAMES.shootScene));
  children.push(Spacer());
}

// 色规表
children.push(H3('色规速查'));
children.push(buildTable(
  ['色彩', '色值', '用途'],
  [
    ['🟡 黄', '#E89B1A', '所有数字（分数 / 名额 / 时长 / 降分）'],
    ['🔴 红', '#C00000', '所有结论（强调 / 反转 / 价值判断）'],
    ['⚪ 白', '#FFFFFF', '旁白逐字稿（普通信息）'],
    ['🟥 品牌红', '#D33A2C', '顶部标题板红框 / 章节大字板背景'],
  ],
  { colWidths: [1500, 1800, 6446] },
));
children.push(Spacer());

// 各条脚本
children.push(H1('📝 脚本详情', '000000'));
SCRIPTS.forEach(s => renderScript(s, children));

// 收尾
children.push(BR());
children.push(new Paragraph({ spacing: { before: 600, after: 0 }, alignment: AlignmentType.CENTER,
  children: [new TextRun({ text: '— 脚本合集 完 —', size: 22, color: C.gray, italics: true, font: FONT })] }));

// 生成
const doc = new Document({
  creator: 'Claude', title: COVER.title,
  styles: {
    default: { document: { run: { font: FONT, size: 22 } } },
    paragraphStyles: [
      { id: 'Heading1', name: 'Heading 1', basedOn: 'Normal', next: 'Normal', quickFormat: true,
        run: { size: 36, bold: true, font: FONT, color: C.brandRed },
        paragraph: { spacing: { before: 360, after: 200 }, outlineLevel: 0 } },
      { id: 'Heading2', name: 'Heading 2', basedOn: 'Normal', next: 'Normal', quickFormat: true,
        run: { size: 28, bold: true, font: FONT },
        paragraph: { spacing: { before: 280, after: 140 }, outlineLevel: 1 } },
      { id: 'Heading3', name: 'Heading 3', basedOn: 'Normal', next: 'Normal', quickFormat: true,
        run: { size: 24, bold: true, font: FONT, color: C.gray },
        paragraph: { spacing: { before: 180, after: 100 }, outlineLevel: 2 } },
    ],
  },
  numbering: {
    config: [
      { reference: 'bullets', levels: [{ level: 0, format: LevelFormat.BULLET, text: '•',
        alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 720, hanging: 360 } } } }] },
      { reference: 'numbers', levels: [{ level: 0, format: LevelFormat.DECIMAL, text: '%1.',
        alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 720, hanging: 360 } } } }] },
    ],
  },
  sections: [{
    properties: { page: { size: { width: PAGE_W, height: PAGE_H },
      margin: { top: MARGIN, right: MARGIN, bottom: MARGIN, left: MARGIN } } },
    children,
  }],
});

const outPath = path.join(__dirname, OUT_NAME);
Packer.toBuffer(doc).then(buf => {
  fs.writeFileSync(outPath, buf);
  console.log(`✓ 已生成 Word: ${outPath} (size: ${buf.length})`);
}).catch(err => {
  console.error('生成失败:', err);
  process.exit(1);
});
