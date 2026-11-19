# API 接口文档

## 视频文案提取 API

**接口地址：** `https://agent.mathmind.cn/minimalist/api/video-audio/recognize`

**请求方式：** POST

**请求头：**
| Header | 值 |
|--------|-----|
| Content-Type | application/json |
| x-api-key | 你的 x-api-key |

**请求参数：**
```json
{
  "videoUrl": "视频公网地址（支持抖音短链接）"
}
```

**响应示例：**
```json
{
  "code": 0,
  "errorMessage": "",
  "text": "提取的文案内容",
  "data": {
    "Duration": 10.041667
  }
}
```

**错误码：**
| code | 含义 |
|------|------|
| 0 | 成功 |
| 401 | APIKEY 错误 |
| 403 | 权限不足 |
| 4xx/5xx | 服务端错误 |

## 视频上传接口

由于本地 .mp4 文件需要先上传到公网，可以使用以下临时存储服务：

### litterbox.catbox.moe（临时，有效期 72 小时）
```bash
curl -s -F "reqtype=fileupload" -F "time=72h" -F "fileToUpload=@/path/to/video.mp4" https://litterbox.catbox.moe/resources/internals/api.php
```

### transfer.sh（需要代理）
```bash
curl --silent --show-error --upload-file "/path/to/video.mp4" "https://transfer.sh/$(basename "/path/to/video.mp4")"
```

### 0x0.st（已禁用）
> 上传功能已暂时禁用。

---

获取 x-api-key：访问 [kexiangai.com](https://kexiangai.com)