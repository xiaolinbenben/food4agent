---
name: parallel-execution
description: 并行执行子技能 - 多引擎并行策略、失败切换、响应时间控制
trigger:
  keywords: [并行, 多引擎, 同时搜索, 并发, fallback]
---

# 并行执行策略

## 可并行组合

### 同类P0引擎并行

| 查询类型 | 并行组合 | 说明 |
|----------|----------|------|
| 技术问题 | CSDN + Stack Overflow | 中英文并行 |
| AI技术 | CSDN + ArXiv | 教程+论文 |
| 学术论文 | 知网 + ArXiv | 中英文学术 |
| 热点新闻 | 百度资讯 + 今日头条 | 多信源热点 |
| 贈经新闻 | 东方财富 + 贈新 | 资讯+深度 |
| A股查询 | 东方财富 + 雪球 | 数据+社区 |
| 基金查询 | 天天基金 + 蛋卷基金 | 数据+社区 |
| 投资策略 | 集思录 + 且慢 | 社区+投顾 |
| 购物比价 | 淘宝 + 京东 | 多平台对比 |
| 汽车查询 | 汽车之家 + 易车 | 多平台评测 |
| 本地商家 | 大众点评 + 百度地图 | 商家+定位 |
| 英文搜索 | Brave + DDG | 隐私友好引擎 |

---

## 执行规则

### 1. 主引擎优先（串行策略）

```javascript
async function search(query) {
  // Step 1: 调用P0主引擎
  let results = await fetch(p0_engine, query);
  if (results.length > 0) return results;

  // Step 2: 调用P1备用引擎
  results = await fetch(p1_engine, query);
  if (results.length > 0) return results;

  // Step 3: 调用B级兜底引擎
  return await fetch(b_engine, query);
}
```

### 2. 并行执行

```javascript
async function parallelSearch(query, engines) {
  // 最多同时调用2个引擎
  const results = await Promise.all([
    fetch(engines[0], query),
    fetch(engines[1], query)
  ]);

  // 合并去重
  return mergeAndDedup(results);
}
```

### 3. 失败切换

```javascript
async function searchWithFallback(query, engines) {
  for (const engine of engines) {
    try {
      const results = await fetch(engine, query, { timeout: 3000 });
      if (results.length > 0) return results;
    } catch (error) {
      console.log(`${engine} failed, trying next...`);
      continue;
    }
  }
  return [];
}
```

---

## 并行限制

| 规则 | 配置 |
|------|------|
| 最大并行数 | 2个引擎 |
| 超时时间 | 3秒 |
| 重试次数 | 1次 |
| 结果合并 | 按权重排序，去重 |

---

## 响应时间要求

| 操作 | 时间限制 |
|------|----------|
| 单引擎请求 | ≤3秒 |
| 并行请求 | ≤5秒 |
| 结果处理 | ≤1秒 |
| 总响应时间 | ≤6秒 |

---

## 异常处理

| 异常类型 | 处理策略 |
|----------|----------|
| 引擎无响应 | 切换备用引擎，记录异常 |
| 超时 | 重试1次，失败后切换引擎 |
| 结果空 | 放宽关键词，扩大引擎范围 |
| 网络异常 | 提示用户，建议重试 |