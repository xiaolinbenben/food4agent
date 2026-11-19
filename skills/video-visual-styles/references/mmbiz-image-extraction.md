# 产品图片提取方法 — mmbiz.qpic.cn

> 来源：2026-07-02 鸟迪支架视频制作
> 适用：所有从公众号文章提取产品图片的场景

## 图片URL特征

微信公众号文章中的产品图片统一使用 `mmbiz.qpic.cn` 域名：

```
http://mmbiz.qpic.cn/sz_mmbiz_jpg/<hash>/0?wx_fmt=jpeg
http://mmbiz.qpic.cn/mmbiz_png/<hash>/0?wx_fmt=png
```

- `sz_mmbiz_jpg` — 原始尺寸JPG
- `mmbiz_png` — PNG格式
- 末尾 `/0` — 表示原始尺寸
- `?wx_fmt=jpeg/png` — 格式标识

## 提取方法

从历史公众号HTML文件中提取：

```bash
# 查找包含产品图的HTML文件
grep -rl 'mmbiz.qpic.cn' /path/to/articles/

# 提取图片URL
grep -o 'src="http[^"]*mmbiz[^"]*"' article.html
```

## 已知产品图片

### 鸟迪出风口支架

| 型号 | 图片URL | 来源文件 |
|------|---------|---------|
| Z20 | `http://mmbiz.qpic.cn/sz_mmbiz_jpg/r192RXtR9OrxBqxhEHfm09dNRuN1Oet6Fib4ybCjdniad1MggmUxpBIETCrxJFD36iaFS0nFetoC3N7rj6dNgB8EsYjTaouEaI3HMooOOlXYbQ/0?wx_fmt=jpeg` | `niaodi_Z20_...html` |
| Z51 | `http://mmbiz.qpic.cn/mmbiz_png/r192RXtR9OrO8RUbhGU5cJ5xAVqUmofUZFDZOLicz7PKN6RiaLvne7xXFqre3HKFDdR6S8JtQDK7Iup8yFoufNSJwZ37qSP95QtBbb4Iq3hK8/0?wx_fmt=png` | `niaodi_Z51_...html` |
| Z33 | `http://mmbiz.qpic.cn/mmbiz_png/r192RXtR9OpTWILguWMYdMic0icTgbaT9RX7icnxL1Q2luReWVECLFxxA3RNzMtFzmGbuRbHnrOU7RIYoNoHADiaJ1Aada143EWK1Y4QDzB6TnU/0?wx_fmt=png` | `niaodi_Z33_...html` |

## 注意事项

1. **HTTP协议**：mmbiz URL是HTTP，HyperFrames编译器warn但不影响runtime渲染
2. **跨域问题**：从本地HTML打开时，Chrome可能阻止HTTP图片加载到HTTPS页面。但在HyperFrames的file://协议下正常
3. **图片过期**：微信图片有CDN缓存期限，长期使用建议下载到本地
4. **尺寸**：公众号图片通常是750px宽，视频渲染时CSS `max-width:100%; object-fit:contain` 自适应
5. **提取位置**：图片URL在`<img src="...">`标签中，紧跟在`<section style="text-align:center;margin:20px 0;">`之后
