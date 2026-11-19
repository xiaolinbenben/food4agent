---
name: education
description: 教育/考试领域 - 考研/公考/高考/课程/论文
version: 4.2.0
---

# 教育领域 v4.2.0

## 领域特征

```
查询类型: 考研/公考/高考/课程/论文/教材/真题
时效要求: 中（考试政策每年更新，真题需最新年份）
权威要求: 高（必须以官方/权威来源为准）
交叉验证: 考试政策/分数线必须多源验证
```

---

## 子类型与引擎

### 考研

| 优先级 | 引擎 | URL模板 | 说明 |
|--------|------|---------|------|
| P0 | 考研帮 | `kaoyan.com/search?keyword=QUERY` | 考研经验+院校信息 |
| P0 | 中国知网 | `cnki.net/search?q=QUERY` | 学术论文+导师论文 |
| P1 | 学堂在线 | `xuetangx.com/search?keyword=QUERY` | 考研课程 |
| P1 | 小红书 | `xiaohongshu.com/search_result?keyword=QUERY` | 考研经验贴 |

### 公考

| 优先级 | 引擎 | URL模板 | 说明 |
|--------|------|---------|------|
| P0 | 粉笔公考 | `fenbi.com/search?keyword=QUERY` | 真题+解析 |
| P1 | 华图教育 | `huatu.com/search?keyword=QUERY` | 备考资料 |
| P1 | 国家公务员局 | `scs.gov.cn/` | 官方招考信息 |

### 高考

| 优先级 | 引擎 | URL模板 | 说明 |
|--------|------|---------|------|
| P0 | 阳光高考 | `gaokao.chsi.com.cn` | 官方信息平台 |
| P0 | 高考网 | `gaokao.com/search?keyword=QUERY` | 志愿填报+分数线 |
| P1 | 掌上高考 | `gk.chsi.com.cn` | 院校查询 |

### 在线课程

| 优先级 | 引擎 | URL模板 | 说明 |
|--------|------|---------|------|
| P0 | 中国大学MOOC | `icourse163.org/search?keyword=QUERY` | 名校课程 |
| P1 | 学堂在线 | `xuetangx.com/search?keyword=QUERY` | 清华课程 |
| P1 | B站 | `search.bilibili.com/all?keyword=QUERY` | 免费教程 |

### 学术论文

| 优先级 | 引擎 | URL模板 | 说明 |
|--------|------|---------|------|
| P0 | 中国知网 | `cnki.net/search?q=QUERY` | 中文学术首选 |
| P0 | 万方数据 | `wanfangdata.com.cn/search/searchList.do?searchWord=QUERY` | 中文学术 |
| P1 | 百度学术 | `xueshu.baidu.com/s?wd=QUERY` | 学术聚合 |
| P1 | 维普 | `cqvip.com/qk/search?kw=QUERY` | 期刊论文 |

---

## 信源权重

```
国家公务员局/教育部      → 权重 1.0  🏢官方
阳光高考/研招网          → 权重 0.95 🏢官方
中国知网/万方/维普       → 权重 0.95 🏢官方
中国大学MOOC/学堂在线    → 权重 0.85 📰权威
考研帮/粉笔/华图         → 权重 0.8  📰权威
B站/小红书经验贴         → 权重 0.6  👥社区
百度知道/贴吧            → 权重 0.4  📝个人
```

---

## 查询改写规则

```
"考研XX"     → "XX考研科目+分数线+院校推荐"
"公考XX"     → "XX公务员考试真题+备考攻略"
"高考XX"     → "XX高考政策+志愿填报"
"XX课程"     → "XX在线课程+评价+免费资源"
"XX论文"     → "XX学术论文+参考文献+研究现状"
```

---

## 特殊规则

```
1. 考试政策/分数线 → 必须交叉验证（政策每年变化）
2. 真题答案 → 必须标注来源（官方解析 > 机构解析 > 网友解析）
3. 院校信息 → 优先采信官方招生网站
4. 课程推荐 → 标注是否免费/付费
5. 论文引用 → 标注发表年份和引用量
```
