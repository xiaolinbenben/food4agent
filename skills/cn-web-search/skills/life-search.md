---
name: life-search
description: 生活类搜索子技能 - 本地服务、购物、出行、天气
trigger:
  keywords: [附近, 地图, 地址, 餐厅, 医院, 银行, 购买, 价格, 商品名, 评测, 天气, 气温, 预报]
---

# 生活类搜索

## 查询类型识别

| 子类型 | 触发关键词 |
|--------|------------|
| 本地服务 | 附近、地图、地址、餐厅、医院、银行 |
| 购物消费 | 购买、价格、商品名、评测、推荐 |
| 天气查询 | 天气、气温、预报、下雨、温度 |
| 出行交通 | 地铁、公交、路线、打车 |

---

## 引擎路由表

### 本地服务

| 优先级 | 引擎 | URL模板 | 说明 |
|--------|------|---------|------|
| P0 | 百度地图 | `https://map.baidu.com/search?query=QUERY` | 地理定位 |
| P0 | 大众点评 | `https://www.dianping.com/search/keyword/1/0_QUERY` | 本地商家 |
| P1 | 高德地图 | `https://www.amap.com/search?query=QUERY` | 地理定位 |
| B | 百度 | `https://www.baidu.com/s?wd=QUERY` | 广泛搜索 |

### 购物消费

| 优先级 | 引擎 | URL模板 | 说明 |
|--------|------|---------|------|
| P0 | 淘宝 | `https://s.taobao.com/search?q=QUERY` | 商品搜索 |
| P0 | 京东 | `https://search.jd.com/Search?keyword=QUERY&enc=utf-8` | 商品搜索 |
| P0 | 什么值得买 | `https://search.smzdm.com/?c=posts&s=QUERY` | 消费决策、评测 |
| P1 | 小红书 | `https://www.xiaohongshu.com/search_result?keyword=QUERY` | 购物攻略 |
| B | 百度 | `https://www.baidu.com/s?wd=QUERY` | 广泛搜索 |

### 天气查询

| 优先级 | 引擎 | URL模板 | 说明 |
|--------|------|---------|------|
| P0 | 百度天气 | `https://www.baidu.com/s?wd=QUERY+天气` | 天气查询 |
| P0 | 中国天气网 | `http://www.weather.com.cn/search?cityname=QUERY` | 官方天气 |
| P1 | 天气通 | `https://tianqi.911cha.com/QUERY.html` | 天气查询 |
| B | 百度 | `https://www.baidu.com/s?wd=QUERY` | 广泛搜索 |

### 汽车出行

| 优先级 | 引擎 | URL模板 | 说明 |
|--------|------|---------|------|
| P0 | 汽车之家 | `https://so.autohome.com.cn/all?q=QUERY` | 汽车评测 |
| P0 | 易车 | `https://search.yiche.com/search.html?keyword=QUERY` | 汽车信息 |
| P1 | 懂车帝 | `https://www.dongchedi.com/search?keyword=QUERY` | 字节生态 |
| B | 百度 | `https://www.baidu.com/s?wd=QUERY` | 广泛搜索 |

### 手机数码

| 优先级 | 引擎 | URL模板 | 说明 |
|--------|------|---------|------|
| P0 | 安兔兔 | `https://www.antutu.com/search?keyword=QUERY` | 手机评测 |
| P0 | ZOL中关村 | `https://search.zol.com.cn/s_all.php?keyword=QUERY` | 数码参数 |
| P1 | 太平洋电脑 | `https://search.pconline.com.cn/?q=QUERY` | 数码评测 |
| B | 百度 | `https://www.baidu.com/s?wd=QUERY` | 广泛搜索 |

---

## 并行策略

| 场景 | 并行组合 | 说明 |
|------|----------|------|
| 购物比价 | 淘宝 + 京东 + 什么值得买 | 多平台对比 |
| 汽车查询 | 汽车之家 + 易车 | 多平台评测 |
| 本地商家 | 大众点评 + 百度地图 | 商家+定位 |

---

## 使用示例

```javascript
// 购物比价（并行）
web_fetch(url="https://s.taobao.com/search?q=机械键盘", maxChars=8000)
web_fetch(url="https://search.jd.com/Search?keyword=机械键盘&enc=utf-8", maxChars=8000)
web_fetch(url="https://search.smzdm.com/?c=posts&s=机械键盘", maxChars=8000)

// 天气查询
web_fetch(url="https://www.baidu.com/s?wd=北京+天气", maxChars=5000)
web_fetch(url="http://www.weather.com.cn/search?cityname=北京", maxChars=5000)

// 本地商家
web_fetch(url="https://www.dianping.com/search/keyword/1/0_火锅", maxChars=8000)

// 汽车评测
web_fetch(url="https://so.autohome.com.cn/all?q=特斯拉Model3评测", maxChars=10000)

// 手机参数
web_fetch(url="https://search.zol.com.cn/s_all.php?keyword=iPhone15参数", maxChars=8000)
```