# 商机图片获取 + 上传流程

## 目标

获取商品图片并上传至飞书，拿到 `file_token`，用于写入 Bitable 附件字段。

## 方法一：直接 URL 上传（推荐，最简单）

当你已有图片 URL（来自浏览器快照、web_search、商机弹窗 JS 提取等）：

```
feishu_doc upload_image url=<图片URL>
```

返回 `file_token`，直接写入 Bitable：
```json
"商机图片": [{"file_token": "返回的file_token"}]
```

## 方法二：下载后上传（URL 有鉴权/防盗链时用）

**Step 1：下载到本地**

```bash
bash {baseDir}/scripts/fetch_image.sh "<URL>"
# 返回本地路径，如 /tmp/openclaw/uploads/img_xxx.jpg
```

**Step 2：上传到飞书**

```
feishu_doc upload_image file_path=<本地路径>
```

返回 `file_token`。

## 方法三：无图片时的降级策略

如果无法获取图片（防盗链严重、JS 提取失败等）：
1. 优先用 `web_search` 搜商品名 + "图片"，找公开图片 URL
2. 实在找不到：`商机图片` 字段留空，在 `评估备注` 注明「暂无图片」

## 抖音商机中心弹窗 JS 提取

```javascript
// 在「商机详情」drawer 打开后执行
// 过滤 p3/p6/tos 开头的商品图 URL，排除 icon/logo
Array.from(document.querySelectorAll('[class*=drawer],[class*=Drawer]'))
  .find(d => d.innerText.includes('商机详情'))
  ?.querySelectorAll('img')
  |> (imgs => Array.from(imgs ?? []).map(i => i.src)
       .filter(s => s.includes('p3') || s.includes('p6') || s.includes('tosv')))
  ?? []
```

取第一个 URL → 走方法一。

> 实测说明（2026-03-11）：`.commodity-modal` 等 class 在新版商机中心已不存在，
> 改用 drawer 容器内过滤 img src 更可靠。防盗链 URL 有效期约 48h，走方法一直接上传即可。

## 注意事项

- 图片文件必须小于 20MB
- 支持格式：jpg / png / webp / gif
- 避免截全屏：文件大且包含无关 UI
