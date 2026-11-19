---
domain: life
keywords: [购物, 附近, 餐厅, 外卖, 天气, 酒店, 机票, 买, 价格, 测评, 推荐, 优惠券]
version: 4.2.0
---

# 生活购物搜索

## 快速路由

| 子类型 | 触发关键词 | P0引擎 | P1引擎 |
|--------|------------|--------|--------|
| 本地生活 | 附近、餐厅、外卖、天气 | 高德 + 大众点评 | 美团 |
| 购物消费 | 买、价格、测评、推荐 | 淘宝 + 京东 | 什么值得买 |
| 出行旅游 | 酒店、机票、旅游 | 12306 + 携程 | 去哪儿 |

---

## 引擎URL模板

| 引擎 | URL模板 | 说明 |
|------|---------|------|
| 高德地图 | `https://www.amap.com/search?query=QUERY&city=CITY` | 地理定位导航（支持城市参数）|
| 大众点评 | `https://www.dianping.com/search/keyword/CITY_ID/0_QUERY` | 本地商家餐饮（CITY_ID: 1北京 2上海 3广州 4深圳）|
| 美团 | `https://i.meituan.com/awp/h5/search?keyword=QUERY&city=CITY` | 本地生活团购（支持城市参数）|
| 和风天气 | `https://www.qweather.com/search?city=CITY` | 专业天气查询 🆕 |
| 中国天气网 | `http://www.weather.com.cn/weather1d/CITY_CODE.shtml` | 官方天气 |
| 12306 | `https://www.12306.cn/index/index.html` | 铁路票务官方 |
| 携程 | `https://www.ctrip.com/search/?keyword=QUERY` | 机票酒店旅游 |
| 淘宝 | `https://s.taobao.com/search?q=QUERY` | 商品搜索首选 |
| 京东 | `https://search.jd.com/Search?keyword=QUERY` | 电商正品保障 |
| 什么值得买 | `https://search.smzdm.com/?c=posts&s=QUERY` | 消费决策评测 |
| 小红书 | `https://www.xiaohongshu.com/search_result?keyword=QUERY` | 种草测评攻略 |

---

## 执行示例

```
本地商家（含城市参数）:
web_fetch(url="https://www.dianping.com/search/keyword/1/0_火锅")
web_fetch(url="https://www.amap.com/search?query=附近餐厅&city=北京")

天气查询（专用引擎）:
web_fetch(url="https://www.qweather.com/search?city=北京")

购物比价（并行）:
web_fetch(url="https://s.taobao.com/search?q=iPhone15")
web_fetch(url="https://search.jd.com/Search?keyword=iPhone15")

消费决策:
web_fetch(url="https://search.smzdm.com/?c=posts&s=笔记本电脑推荐")

出行:
web_fetch(url="https://www.ctrip.com/search/?keyword=三亚酒店")
```

---

## 并行策略

| 场景 | 并行组合 | 说明 |
|------|----------|------|
| 购物比价 | 淘宝 + 京东 | 多平台对比 |
| 本地商家 | 大众点评 + 高德 | 商家+定位 |
| 消费决策 | 什么值得买 + 小红书 | 评测+种草 |

---

## 信源权重

```
官方平台（12306、航空公司官网）   → 权重 1.0
本地生活（大众点评、美团）        → 权重 0.85
电商平台（淘宝、京东）            → 权重 0.8
消费决策（什么值得买）            → 权重 0.75
社交种草（小红书）                → 权重 0.6
```