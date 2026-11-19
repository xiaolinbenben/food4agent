#!/usr/bin/env python3
"""
TikTok 东南亚选品 Agent - 可调度自动化数据采集脚本
=====================================================
工具链：
  OpenCLI  — 公开数据 + 需登录的结构化平台数据（TikTok / Amazon / Reddit / 小红书 / 1688）

数据流：
  OpenCLI 采集真实数据
       ↓
  AI 分析（LLM 基于真实数据生成选品建议）
       ↓
  POST /api/trpc/dataSync.recordRun → 平台数据库

调度方式（由 Manus schedule 工具管理）：
  每日 08:00 快速更新：cron "0 0 8 * * *"
  每日 20:00 标准采集：cron "0 0 20 * * *"
  每周一深度分析：    cron "0 0 6 * * 1"

手动触发：
  python sea_product_agent.py --mode quick
  python sea_product_agent.py --mode standard --write-db --platform-url https://your-platform.manus.space
  python sea_product_agent.py --mode deep --categories beauty,fashion --countries ID,TH

依赖安装：
  npm install -g @jackwener/opencli
"""

import argparse
from enum import Enum
import json
import logging
import os
import re
import shlex
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

# ============================================================
# 默认配置
# ============================================================

DEFAULT_CATEGORIES = ["beauty", "fashion", "home", "electronics", "health"]
DEFAULT_COUNTRIES = ["ID", "TH", "VN", "PH", "MY"]

COUNTRY_NAMES = {
    "ID": "Indonesia",
    "TH": "Thailand",
    "VN": "Vietnam",
    "PH": "Philippines",
    "MY": "Malaysia",
}

CATEGORY_KEYWORDS = {
    "beauty": {"en": "skincare", "zh": "美妆护肤", "tiktok_tag": "beautyproducts"},
    "fashion": {"en": "fashion", "zh": "服饰穿搭", "tiktok_tag": "fashiontiktok"},
    "home": {"en": "home decor", "zh": "家居用品", "tiktok_tag": "homedecor"},
    "electronics": {"en": "gadgets", "zh": "数码3C", "tiktok_tag": "techreview"},
    "health": {"en": "supplements", "zh": "健康保健", "tiktok_tag": "healthtips"},
    "baby": {"en": "baby", "zh": "母婴用品", "tiktok_tag": "babytiktok"},
    "food": {"en": "snacks", "zh": "食品零食", "tiktok_tag": "foodtiktok"},
}

STOP_WORDS = {
    "the",
    "and",
    "for",
    "with",
    "from",
    "viral",
    "tiktok",
    "shop",
    "official",
    "new",
    "best",
    "hot",
    "sale",
    "product",
    "products",
    "review",
    "home",
    "decor",
    "fashion",
    "beauty",
    "health",
    "gadgets",
    "skincare",
    "supplements",
}

# 评分参数说明：所有基础分尽量压到 0-100 区间，再按权重组合成 potentialScore。
# - profit_score: 利润空间得分，0-100
# - search_growth: 搜索/趋势热度代理值，0-100
# - competition_score: 竞争度得分，0-100，越低竞争越高分
# - sentiment_score: 内容情绪代理值，0-100
# hot_signal 是高销量和高趋势的额外加成，用于放大明显值得关注的候选品。
DEFAULT_FX_CNY_USD = 0.14
LANDED_MARKUP_MULTIPLIER = 3.5
PROFIT_WEIGHT = 0.35
SEARCH_GROWTH_WEIGHT = 0.30
COMPETITION_WEIGHT = 0.20
SENTIMENT_WEIGHT = 0.15
HIGH_SALES_VOLUME_THRESHOLD = 5000
MEDIUM_SALES_VOLUME_THRESHOLD = 1000
HIGH_SEARCH_GROWTH_THRESHOLD = 50
MEDIUM_SEARCH_GROWTH_THRESHOLD = 25
HIGH_HOT_SIGNAL_BONUS = 20
MEDIUM_HOT_SIGNAL_BONUS = 10
HOT_SIGNAL_TRUST_MULTIPLIER = {
    "official": 1.0,
    "verified": 0.85,
    "proxy": 0.6,
}


class Provider(str, Enum):
    OPENCLI = "opencli"
    DIRECT = "direct"
    SNAPSHOT = "snapshot"


class SourceTrust(str, Enum):
    OFFICIAL = "official"
    VERIFIED = "verified"
    PROXY = "proxy"


_BASE_DIR = Path(
    os.environ.get("SEA_DATA_DIR", str(Path.home() / ".sea_data"))
).expanduser()
LOG_DIR = _BASE_DIR / "logs"
DATA_DIR = _BASE_DIR / "runs"

DATA_SOURCE_CAPABILITIES = {
    "google_trends": {"mode": "quick", "provider": Provider.OPENCLI},
    "google_news": {"mode": "quick", "provider": Provider.OPENCLI},
    "tiktok": {"mode": "standard", "provider": Provider.OPENCLI},
    "custom_source": {"mode": "standard", "provider": Provider.SNAPSHOT},
    "amazon": {"mode": "deep", "provider": Provider.OPENCLI},
    "reddit": {"mode": "deep", "provider": Provider.OPENCLI},
    "xiaohongshu": {"mode": "deep", "provider": Provider.OPENCLI},
    "1688": {"mode": "deep", "provider": Provider.OPENCLI},
}

# ============================================================
# 日志设置
# ============================================================


def setup_logging(run_id: str) -> logging.Logger:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    log_file = LOG_DIR / f"agent_{run_id}.log"
    latest_lnk = LOG_DIR / "latest.log"

    try:
        if latest_lnk.exists() or latest_lnk.is_symlink():
            latest_lnk.unlink()
        latest_lnk.symlink_to(log_file.resolve())
    except Exception:
        pass

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.FileHandler(log_file, encoding="utf-8"),
            logging.StreamHandler(sys.stdout),
        ],
    )
    return logging.getLogger("sea_agent")


# ============================================================
# 命令执行工具
# ============================================================


def run_cmd(cmd: list, timeout: int = 60) -> Optional[Any]:
    """执行 CLI 命令，返回解析后的 JSON 数据。"""
    logger = logging.getLogger("sea_agent")
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        if r.returncode == 0 and r.stdout.strip():
            try:
                return json.loads(r.stdout)
            except json.JSONDecodeError:
                # 部分命令输出非 JSON，返回原始文本
                return {"raw": r.stdout.strip()}
        if r.returncode != 0:
            stderr = (r.stderr or "").strip()
            logger.info(
                "命令执行失败: cmd=%s exit=%s stderr=%s",
                " ".join(cmd),
                r.returncode,
                stderr[:500],
            )
            return None
    except subprocess.TimeoutExpired as exc:
        logger.debug("命令执行超时: cmd=%s timeout=%ss", " ".join(cmd), timeout)
        if exc.stderr:
            logger.debug("命令超时 stderr=%s", str(exc.stderr)[:500])
    except FileNotFoundError:
        logger.debug("命令不存在: cmd=%s", " ".join(cmd))
    return None


def run_opencli(args: list, timeout: int = 60) -> Optional[Any]:
    """
    执行 opencli 命令。
    正确格式：opencli <platform> <subcommand> [positional_arg] [--flags] -f json
    注意：参数必须是位置参数，不能用 --query / --geo 等不存在的 flag。
    """
    cmd = ["opencli"] + args + ["-f", "json"]
    return run_cmd(cmd, timeout=timeout)


def load_json_file(file_path: str) -> Optional[Any]:
    try:
        with open(Path(file_path).expanduser(), "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def run_json_command(command: str, timeout: int = 90) -> Optional[Any]:
    try:
        parsed = shlex.split(command)
    except ValueError:
        return None
    return run_cmd(parsed, timeout=timeout)


def check_opencli_bridge() -> bool:
    """检查 OpenCLI Browser Bridge 是否已连接（需要 Chrome 扩展）"""
    try:
        r = subprocess.run(
            ["opencli", "doctor"], capture_output=True, text=True, timeout=10
        )
        return r.returncode == 0 and "connected" in r.stdout.lower()
    except Exception:
        return False


def _run_lightweight_opencli_probe(
    command: list[str], timeout: int = 10
) -> Optional[int]:
    try:
        result = subprocess.run(
            command, capture_output=True, text=True, timeout=timeout
        )
        return result.returncode
    except Exception:
        return None


def _check_platform_access(
    name: str,
    lightweight_cmds: list[list[str]],
    fallback_cmd: list[str],
    logger: logging.Logger,
) -> str:
    for cmd in lightweight_cmds:
        exit_code = _run_lightweight_opencli_probe(["opencli"] + cmd)
        if exit_code is None:
            continue
        if exit_code == 0:
            logger.info(f"│ {name:<16} : ✅ 已就绪（轻量探测）")
            return "ok"
        if exit_code == 77:
            logger.warning(f"│ {name:<16} : ❌ 未登录 → 请在 Chrome 中登录对应站点")
            return "not_logged_in"

    exit_code = _run_lightweight_opencli_probe(
        ["opencli"] + fallback_cmd + ["-f", "json"], timeout=15
    )
    if exit_code == 0:
        logger.info(f"│ {name:<16} : ✅ 已登录")
        return "ok"
    if exit_code == 77:
        logger.warning(f"│ {name:<16} : ❌ 未登录 → 请在 Chrome 中登录对应站点")
        return "not_logged_in"
    if exit_code is None:
        logger.warning(f"│ {name:<16} : ⚠️  检测超时")
        return "error"

    logger.warning(f"│ {name:<16} : ⚠️  异常 (exit {exit_code})")
    return "error"


def run_preflight_check(
    mode: str, logger: logging.Logger, skip_preflight: bool = False
) -> dict:
    """
    启动自检：检查 OpenCLI 连通性及各平台登录状态。
    返回 {platform: "ok"|"not_logged_in"|"no_adapter"|"error"} 字典。
    """
    if skip_preflight:
        logger.info("跳过环境自检（--skip-preflight）")
        return {"bridge": check_opencli_bridge(), "skipped": True}

    logger.info("╭─ 环境自检 ──────────────────────────────╮")

    # 1. 检查 opencli 是否安装
    try:
        r = subprocess.run(
            ["opencli", "--version"], capture_output=True, text=True, timeout=5
        )
        opencli_ver = r.stdout.strip() if r.returncode == 0 else "未知"
        logger.info(f"│ OpenCLI 版本     : ✅ {opencli_ver}")
    except FileNotFoundError:
        logger.error("│ OpenCLI          : ❌ 未安装 → npm i -g @jackwener/opencli")
        logger.info("╰─────────────────────────────────────────╯")
        return {"opencli": "missing"}

    # 2. 检查 Browser Bridge
    bridge_ok = check_opencli_bridge()
    if bridge_ok:
        logger.info("│ Browser Bridge   : ✅ 已连接")
    else:
        logger.warning(
            "│ Browser Bridge   : ❌ 未连接 → 安装 Chrome 扩展或使用 OpenClaw"
        )

    # 3. 按模式检查各平台登录状态
    # quick 模式不需要登录任何站点
    platforms_to_check = []
    if mode in ("standard", "deep"):
        platforms_to_check.append(
            (
                "TikTok",
                [
                    ["tiktok", "auth", "status"],
                    ["tiktok", "status"],
                    ["tiktok", "explore", "--help"],
                ],
                ["tiktok", "explore", "--limit", "1"],
            )
        )
    if mode == "deep":
        platforms_to_check.extend(
            [
                (
                    "Amazon",
                    [
                        ["amazon", "auth", "status"],
                        ["amazon", "status"],
                        ["amazon", "bestsellers", "--help"],
                    ],
                    ["amazon", "bestsellers", "--limit", "1"],
                ),
                (
                    "Reddit",
                    [
                        ["reddit", "auth", "status"],
                        ["reddit", "status"],
                        ["reddit", "search", "--help"],
                    ],
                    ["reddit", "search", "test", "--limit", "1"],
                ),
                (
                    "小红书",
                    [
                        ["xiaohongshu", "auth", "status"],
                        ["xiaohongshu", "status"],
                        ["xiaohongshu", "search", "--help"],
                    ],
                    ["xiaohongshu", "search", "测试", "--limit", "1"],
                ),
            ]
        )
        if _has_opencli_command("1688"):
            platforms_to_check.append(
                (
                    "1688",
                    [
                        ["1688", "auth", "status"],
                        ["1688", "status"],
                        ["1688", "search", "--help"],
                    ],
                    ["1688", "search", "测试", "--limit", "1"],
                )
            )
        else:
            logger.warning("│ 1688             : ⚠️  适配器不可用（需 OpenCLI ≥ 1.6.9）")

    status = {"bridge": bridge_ok}
    for name, lightweight_cmds, fallback_cmd in platforms_to_check:
        if not bridge_ok:
            logger.warning(f"│ {name:<16} : ❌ 跳过（Bridge 未连接）")
            status[name] = "no_bridge"
            continue
        status[name] = _check_platform_access(
            name, lightweight_cmds, fallback_cmd, logger
        )

    logger.info("╰─────────────────────────────────────────╯")
    return status


# ============================================================
# 阶段一：OpenCLI 公开数据（无需 Browser Bridge）
# ============================================================


def collect_google_trends(
    categories: list, countries: list, logger: logging.Logger
) -> dict:
    """
    采集 Google Trends 热搜词（无需登录）
    ✅ 正确命令：opencli google trends --region {CODE} --limit 20 -f json
    ❌ 错误：google trends 不接受位置参数关键词，不能用 --query / --geo
    注意：返回的是该国当日热搜榜，不能按品类关键词过滤
    """
    logger.info("  [Google Trends] 开始采集")
    result = {}

    for country in countries:
        # 正确格式：只用 --region 和 --limit，不传关键词位置参数
        data = run_opencli(["google", "trends", "--region", country, "--limit", "20"])
        if data:
            result[country] = data
            count = len(data) if isinstance(data, list) else 1
            logger.info(f"    ✅ Google Trends [{country}]: {count} 条热搜")
        else:
            logger.warning(f"    ⚠️  Google Trends [{country}]: 无数据")
        time.sleep(1)

    return result


def collect_google_news(
    categories: list, countries: list, logger: logging.Logger
) -> dict:
    """
    采集 Google News（无需登录），按目标 SEA 国家拉取。
    ✅ opencli google news [keyword] --region {CC} --lang en --limit 10 -f json
       keyword 是可选位置参数（直接写，不加 --query）
    返回结构：{cat: {country: data}}
    """
    logger.info("  [Google News] 开始采集")
    result: dict = {}

    news_queries = {
        "beauty": "skincare viral tiktok",
        "fashion": "fashion trend viral",
        "home": "home decor trending tiktok",
        "electronics": "wireless earbuds tiktok viral",
        "health": "health supplements trending",
        "baby": "baby products trending",
        "food": "snacks food viral tiktok",
    }

    for cat in categories:
        kw = news_queries.get(
            cat, f"{CATEGORY_KEYWORDS.get(cat, {}).get('en', cat)} viral tiktok"
        )
        result[cat] = {}
        # 仅取前 3 个国家，避免在 quick 模式拉太久
        for country in countries[:3]:
            data = run_opencli(
                [
                    "google",
                    "news",
                    kw,
                    "--region",
                    country,
                    "--lang",
                    "en",
                    "--limit",
                    "10",
                ]
            )
            if data:
                result[cat][country] = data
                count = len(data) if isinstance(data, list) else 1
                logger.info(f"    ✅ Google News [{country}] '{cat}': {count} 条")
            else:
                logger.warning(f"    ⚠️  Google News [{country}] '{cat}': 无数据")
            time.sleep(1)

    return result


# ============================================================
# 阶段二：OpenCLI 需 Browser Bridge 的数据源
# ============================================================


def collect_tiktok(categories: list, countries: list, logger: logging.Logger) -> dict:
    """
    采集 TikTok 数据（需要 OpenCLI Browser Bridge 已连接）
    正确命令：
      opencli tiktok search <query> [--limit N] -f json
      opencli tiktok explore [--limit N] -f json
    """
    logger.info("  [TikTok] 开始采集")
    result = {"explore": None, "search": {}}

    # TikTok 探索页热门
    explore = run_opencli(["tiktok", "explore", "--limit", "30"], timeout=90)
    if explore:
        result["explore"] = explore
        count = len(explore) if isinstance(explore, list) else 1
        logger.info(f"    ✅ TikTok Explore: {count} 条热门内容")
    else:
        logger.warning("    ⚠️  TikTok Explore: 失败（检查 Browser Bridge 连接）")

    # TikTok 品类搜索
    for cat in categories:
        kw = CATEGORY_KEYWORDS.get(cat, {}).get("en", cat)
        result["search"][cat] = {}
        for country in countries[:2]:  # 每品类只采集前两个国家
            query = f"{kw} {COUNTRY_NAMES.get(country, country)}"
            data = run_opencli(["tiktok", "search", query, "--limit", "20"], timeout=90)
            if data:
                result["search"][cat][country] = data
                count = len(data) if isinstance(data, list) else 1
                logger.info(f"    ✅ TikTok Search [{country}] '{kw}': {count} 条")
            else:
                logger.warning(f"    ⚠️  TikTok Search [{country}] '{kw}': 失败")
            time.sleep(2)

    return result


def collect_custom_source(
    categories: list, countries: list, logger: logging.Logger
) -> dict:
    """
    通用外部数据注入口。

    该数据源默认不依赖 OpenCLI，用于把外部抓取结果接入当前结构化评分链路：
    - SEA_CUSTOM_SOURCE_SNAPSHOT: 读取本地 JSON 快照
    - SEA_CUSTOM_SOURCE_COMMAND: 执行外部命令并读取 JSON 输出

    预期返回结构：{category: {country: [item, ...]}}

    注意：这里不为任何单一来源定义专属 schema。它和其他数据源一样，
    只需要提取原始字段并返回；后续统一由 _coerce_product_source / _score_product
    做归一化与评分。

    常见可识别字段包括：
    - title / name
    - price / currentPrice / salePrice
    - soldCount / orders / orderCount / monthlySales
    - trendScore / hotScore / searchGrowthRate
    - imageUrl / image / cover
    """
    logger.info("  [Custom Source] 开始采集")

    snapshot_path = os.environ.get("SEA_CUSTOM_SOURCE_SNAPSHOT")
    if snapshot_path:
        data = load_json_file(snapshot_path)
        if isinstance(data, dict):
            logger.info("    ✅ Custom Source: 已从本地快照加载")
            return data
        logger.warning("    ⚠️  Custom Source: 本地快照格式无效")

    command = os.environ.get("SEA_CUSTOM_SOURCE_COMMAND")
    if command:
        data = run_json_command(command, timeout=120)
        if isinstance(data, dict):
            logger.info("    ✅ Custom Source: 已从外部命令加载")
            return data
        logger.warning("    ⚠️  Custom Source: 外部命令未返回有效 JSON")

    logger.info("    ℹ️  Custom Source: 当前未配置直接采集器，跳过")
    return {category: {country: [] for country in countries} for category in categories}


def collect_amazon(categories: list, logger: logging.Logger) -> dict:
    """
    采集 Amazon 畅销榜（需要 Browser Bridge）
    正确命令：opencli amazon bestsellers [category_path] [--limit N] -f json
    """
    logger.info("  [Amazon] 开始采集畅销榜")
    result = {}

    category_paths = {
        "beauty": "/gp/bestsellers/beauty/",
        "fashion": "/gp/bestsellers/apparel/",
        "home": "/gp/bestsellers/home-garden/",
        "electronics": "/gp/bestsellers/electronics/",
        "health": "/gp/bestsellers/hpc/",
        "baby": "/gp/bestsellers/baby/",
        "food": "/gp/bestsellers/grocery/",
    }

    for cat in categories[:4]:  # 最多采集 4 个品类
        path = category_paths.get(cat, "")
        cmd_args = ["amazon", "bestsellers", "--limit", "20"]
        if path:
            cmd_args = ["amazon", "bestsellers", path, "--limit", "20"]

        data = run_opencli(cmd_args, timeout=120)
        if data:
            result[cat] = data
            count = len(data) if isinstance(data, list) else 1
            logger.info(f"    ✅ Amazon Bestsellers '{cat}': {count} 条")
        else:
            logger.warning(f"    ⚠️  Amazon Bestsellers '{cat}': 失败")
        time.sleep(2)

    return result


def collect_reddit(categories: list, logger: logging.Logger) -> dict:
    """
    采集 Reddit 情绪数据（需要 Browser Bridge）
    正确命令：opencli reddit search <query> [--sort top] [--time month] [--limit N] -f json
    """
    logger.info("  [Reddit] 开始采集情绪数据")
    result = {}

    for cat in categories[:4]:
        kw = CATEGORY_KEYWORDS.get(cat, {}).get("en", cat)
        query = f"{kw} review recommendation southeast asia"
        # 正确格式：位置参数传 query，--sort 和 --time 是合法 flag
        data = run_opencli(
            [
                "reddit",
                "search",
                query,
                "--sort",
                "top",
                "--time",
                "month",
                "--limit",
                "20",
            ],
            timeout=90,
        )
        if data:
            result[cat] = data
            count = len(data) if isinstance(data, list) else 1
            logger.info(f"    ✅ Reddit '{cat}': {count} 条")
        else:
            logger.warning(f"    ⚠️  Reddit '{cat}': 失败（可能需要登录）")
        time.sleep(1.5)

    return result


def collect_xiaohongshu(categories: list, logger: logging.Logger) -> dict:
    """
    采集小红书（需要 Browser Bridge）
    正确命令：opencli xiaohongshu search <query> [--limit N] -f json
    """
    logger.info("  [小红书] 开始采集")
    result = {}

    for cat in categories[:4]:
        zh_kw = CATEGORY_KEYWORDS.get(cat, {}).get("zh", cat)
        data = run_opencli(
            ["xiaohongshu", "search", zh_kw, "--limit", "20"], timeout=90
        )
        if data:
            result[cat] = data
            count = len(data) if isinstance(data, list) else 1
            logger.info(f"    ✅ 小红书 '{zh_kw}': {count} 条")
        else:
            logger.warning(f"    ⚠️  小红书 '{zh_kw}': 失败")
        time.sleep(2)

    return result


# ============================================================
# 阶段三：1688 供货价
# ============================================================


def _has_opencli_command(platform: str) -> bool:
    """检查 opencli 是否有该平台的适配器（通过 list 输出判断）"""
    try:
        r = subprocess.run(
            ["opencli", "list"], capture_output=True, text=True, timeout=10
        )
        # list 输出每行一个适配器名称，要求首列精确等于目标平台
        return any(
            line.split()[0] == platform
            for line in r.stdout.splitlines()
            if line.strip()
        )
    except Exception:
        return False


def collect_1688(categories: list, logger: logging.Logger) -> dict:
    """
    采集 1688 供货价（需要 OpenCLI ≥ 1.6.9 + Browser Bridge + Chrome 已登录 1688.com）
    ✅ opencli 1688 search <query> [--limit N] -f json
    用途：与 Amazon/TikTok 售价对比，估算利润空间
    """
    logger.info("  [1688] 开始采集供货价")

    if not _has_opencli_command("1688"):
        logger.warning(
            "  ⚠️  跳过 1688（当前 OpenCLI 版本无 1688 适配器，需升级到 ≥ 1.6.9）"
        )
        logger.warning("     → npm install -g @jackwener/opencli")
        return {}

    result = {}
    for cat in categories[:4]:
        zh_kw = CATEGORY_KEYWORDS.get(cat, {}).get("zh", cat)
        data = run_opencli(["1688", "search", zh_kw, "--limit", "20"], timeout=120)
        if data:
            result[cat] = data
            count = len(data) if isinstance(data, list) else 1
            logger.info(f"    ✅ 1688 '{zh_kw}': {count} 条")
        else:
            logger.warning(f"    ⚠️  1688 '{zh_kw}': 失败（需要 Chrome 登录 1688.com）")
        time.sleep(2)

    return result


# ============================================================
# 阶段四：结构化候选产品与评分
# ============================================================


def _to_float(value: Any) -> Optional[float]:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        cleaned = value.strip().replace(",", "")
        match = re.search(r"-?\d+(?:\.\d+)?", cleaned)
        if match:
            try:
                return float(match.group())
            except ValueError:
                return None
    return None


def _to_int(value: Any) -> Optional[int]:
    parsed = _to_float(value)
    if parsed is None:
        return None
    return int(parsed)


def _first_present(item: dict, keys: list[str]) -> Any:
    for key in keys:
        if key in item and item[key] not in (None, "", []):
            return item[key]
    return None


def _extract_title(item: dict) -> str:
    value = _first_present(
        item, ["title", "name", "desc", "description", "productName", "itemName"]
    )
    if isinstance(value, str):
        return re.sub(r"\s+", " ", value).strip()
    if isinstance(value, dict):
        return re.sub(r"\s+", " ", json.dumps(value, ensure_ascii=False)).strip()
    return ""


def _extract_image(item: dict) -> Optional[str]:
    value = _first_present(
        item, ["imageUrl", "image", "img", "cover", "coverUrl", "thumbnail", "pic"]
    )
    return value if isinstance(value, str) else None


def _extract_evidence_links(item: dict) -> list[str]:
    candidates = []
    for key in ["url", "item_url", "source_url", "seller_url"]:
        value = item.get(key)
        if isinstance(value, str) and value:
            candidates.append(value)
    return list(dict.fromkeys(candidates))[:3]


def _resolve_trust_level(source: str, item: dict) -> SourceTrust:
    raw = item.get("trustLevel") if isinstance(item, dict) else None
    if isinstance(raw, str):
        try:
            return SourceTrust(raw)
        except ValueError:
            pass
    if source == "custom_source":
        return SourceTrust.VERIFIED
    return SourceTrust.PROXY


def _extract_tags(item: dict, category: str) -> list[str]:
    tags = []
    raw = _first_present(item, ["tags", "hashtags", "keywords"])
    if isinstance(raw, list):
        tags.extend(str(tag) for tag in raw[:5] if tag)
    title = _extract_title(item)
    if title:
        lowered = title.lower()
        if "viral" in lowered:
            tags.append("viral")
        if "tiktok" in lowered:
            tags.append("tiktok")
    tags.append(category)
    return list(dict.fromkeys(tags))[:6]


def _normalize_name(name: str) -> str:
    lowered = name.lower()
    lowered = re.sub(r"[^\w\u4e00-\u9fff]+", " ", lowered)
    return re.sub(r"\s+", " ", lowered).strip()


def _name_tokens(name: str) -> set[str]:
    normalized = _normalize_name(name)
    tokens = {
        token
        for token in normalized.split()
        if len(token) >= 3 and token not in STOP_WORDS
    }
    return tokens


def _median(values: list[float]) -> Optional[float]:
    clean = sorted(v for v in values if v is not None)
    if not clean:
        return None
    mid = len(clean) // 2
    if len(clean) % 2 == 1:
        return clean[mid]
    return (clean[mid - 1] + clean[mid]) / 2


def _build_category_benchmarks(collected: dict, categories: list[str]) -> dict:
    benchmarks: dict[str, dict[str, Any]] = {}
    for category in categories:
        amazon_items = collected.get("amazon", {}).get(category, [])
        supply_items = collected.get("1688", {}).get(category, [])
        news_items = collected.get("google_news", {}).get(category, {})

        amazon_prices = [
            _to_float(_first_present(item, ["price", "currentPrice", "salePrice"]))
            for item in amazon_items
            if isinstance(item, dict)
        ]
        supply_prices = [
            _to_float(_first_present(item, ["price", "priceText", "salePrice"]))
            for item in supply_items
            if isinstance(item, dict)
        ]

        benchmarks[category] = {
            "amazon_price": _median([p for p in amazon_prices if p is not None]),
            "amazon_count": len(amazon_items) if isinstance(amazon_items, list) else 0,
            "supply_price_cny": _median([p for p in supply_prices if p is not None]),
            "supply_count": len(supply_items) if isinstance(supply_items, list) else 0,
            "news_count": sum(
                len(items) for items in news_items.values() if isinstance(items, list)
            )
            if isinstance(news_items, dict)
            else 0,
        }
    return benchmarks


def _estimate_landed_cost_usd(supply_price_cny: Optional[float]) -> Optional[float]:
    if not supply_price_cny or supply_price_cny <= 0:
        return None
    base_usd = supply_price_cny * DEFAULT_FX_CNY_USD
    return round(base_usd * LANDED_MARKUP_MULTIPLIER, 2)


def _normalize_search_index(search_growth_rate: float) -> int:
    return max(0, min(100, int(search_growth_rate)))


def _match_score(source_name: str, candidate_name: str, category: str) -> float:
    source_tokens = _name_tokens(source_name)
    candidate_tokens = _name_tokens(candidate_name)
    if not source_tokens or not candidate_tokens:
        return 0.0

    overlap = source_tokens & candidate_tokens
    base = len(overlap) / max(1, min(len(source_tokens), len(candidate_tokens)))
    if category in source_tokens and category in candidate_tokens:
        base += 0.15
    return min(1.0, base)


def _find_best_match(
    candidate_name: str, items: list[dict], category: str
) -> Optional[dict]:
    best_item = None
    best_score = 0.0
    for item in items:
        if not isinstance(item, dict):
            continue
        item_name = _extract_title(item)
        if not item_name:
            continue
        score = _match_score(item_name, candidate_name, category)
        if score > best_score:
            best_score = score
            best_item = item
    return best_item if best_score >= 0.34 else None


def _score_product(product: dict, benchmark: dict) -> dict:
    matched_amazon = product.get("matchedAmazon") or {}
    matched_1688 = product.get("matched1688") or {}

    price = (
        product.get("price")
        or _to_float(
            _first_present(matched_amazon, ["price", "currentPrice", "salePrice"])
        )
        or benchmark.get("amazon_price")
        or 0
    )
    actual_sales_volume = product.get("salesVolume")
    sales_signal = actual_sales_volume or product.get("engagementProxy") or 0
    search_growth = product.get("searchGrowthRate") or 0
    sentiment_score = product.get("sentimentScore") or 50
    trust_level = product.get("trustLevel") or SourceTrust.PROXY.value

    supply_price_cny = _to_float(
        _first_present(matched_1688, ["price", "priceText", "salePrice"])
    ) or benchmark.get("supply_price_cny")
    landed_cost = _estimate_landed_cost_usd(supply_price_cny)
    if price and landed_cost and price > 0:
        margin_ratio = max(0.0, min(1.0, (price - landed_cost) / price))
    else:
        margin_ratio = 0.35
    profit_score = round(margin_ratio * 100, 1)

    matched_review_count = (
        _to_int(
            _first_present(matched_amazon, ["reviewCount", "reviews", "ratingCount"])
        )
        or 0
    )
    supply_pressure = min(
        25, (benchmark.get("supply_count", 0) + (8 if matched_1688 else 0)) * 2
    )
    amazon_pressure = min(
        45, benchmark.get("amazon_count", 0) * 1.5 + min(15, matched_review_count / 400)
    )
    competition_score = max(
        20, min(90, int(100 - min(70, supply_pressure + amazon_pressure)))
    )

    hot_signal = 0
    if sales_signal >= HIGH_SALES_VOLUME_THRESHOLD:
        hot_signal += HIGH_HOT_SIGNAL_BONUS
    elif sales_signal >= MEDIUM_SALES_VOLUME_THRESHOLD:
        hot_signal += MEDIUM_HOT_SIGNAL_BONUS
    if search_growth >= HIGH_SEARCH_GROWTH_THRESHOLD:
        hot_signal += HIGH_HOT_SIGNAL_BONUS
    elif search_growth >= MEDIUM_SEARCH_GROWTH_THRESHOLD:
        hot_signal += MEDIUM_HOT_SIGNAL_BONUS
    hot_signal *= HOT_SIGNAL_TRUST_MULTIPLIER[trust_level]

    potential_score = round(
        profit_score * PROFIT_WEIGHT
        + search_growth * SEARCH_GROWTH_WEIGHT
        + competition_score * COMPETITION_WEIGHT
        + sentiment_score * SENTIMENT_WEIGHT
        + hot_signal,
        1,
    )
    potential_score = max(1, min(99, int(potential_score)))

    product["competitionScore"] = competition_score
    product["potentialScore"] = potential_score
    product["searchIndex"] = _normalize_search_index(search_growth)
    product["gmv"] = round(price * sales_signal, 2) if price and sales_signal else 0
    product["priceMin"] = round(price * 0.85, 2) if price else None
    product["priceMax"] = round(price * 1.15, 2) if price else None
    product["sellerCount"] = max(
        1, benchmark.get("amazon_count", 0) + benchmark.get("supply_count", 0)
    )
    product["isHot"] = (
        sales_signal >= MEDIUM_SALES_VOLUME_THRESHOLD or potential_score >= 75
    )
    product["isTrending"] = search_growth >= 25 or potential_score >= 80
    if price:
        product["price"] = round(price, 2)
    return product


def _coerce_product_source(
    item: dict, category: str, country: str, source: str
) -> Optional[dict]:
    """把不同来源的原始 item 映射到平台通用产品字段。"""
    name = _extract_title(item)
    if not name:
        return None

    price = _to_float(
        _first_present(item, ["price", "currentPrice", "salePrice", "priceMin"])
    )
    sales_volume = (
        _to_int(
            _first_present(
                item,
                ["salesVolume", "soldCount", "orders", "orderCount", "monthlySales"],
            )
        )
        or 0
    )
    sales_growth_rate = (
        _to_float(
            _first_present(item, ["salesGrowthRate", "growthRate", "trendGrowth"])
        )
        or 0
    )
    sentiment_score = (
        _to_int(_first_present(item, ["sentimentScore", "ratingScore"])) or 60
    )
    search_growth_rate = (
        _to_int(_first_present(item, ["searchGrowthRate", "trendScore", "hotScore"]))
        or 35
    )
    trust_level = _resolve_trust_level(source, item)
    raw_sales_volume = sales_volume if trust_level != SourceTrust.PROXY else None

    return {
        "name": name[:255],
        "nameEn": (_first_present(item, ["nameEn", "titleEn"]) or name)[:255],
        "category": category,
        "country": country,
        "imageUrl": _extract_image(item),
        "price": round(price, 2) if price else None,
        "salesVolume": raw_sales_volume,
        "engagementProxy": sales_volume,
        "salesGrowthRate": round(sales_growth_rate, 1),
        "sentimentScore": sentiment_score,
        "searchIndex": _normalize_search_index(search_growth_rate),
        "searchGrowthRate": search_growth_rate,
        "tags": _extract_tags(item, category) + [source],
        "salesSource": source,
        "trustLevel": trust_level.value,
        "evidenceLinks": _extract_evidence_links(item),
        "source": f"agent:{source}",
    }


def build_structured_products(
    collected: dict, categories: list, countries: list, logger: logging.Logger
) -> list[dict]:
    logger.info("  [产品结构化] 生成候选产品")
    benchmarks = _build_category_benchmarks(collected, categories)
    products: list[dict] = []
    seen: set[tuple[str, str, str]] = set()

    custom_source = collected.get("custom_source", {})
    for category in categories:
        category_benchmark = benchmarks.get(category, {})
        amazon_items = (
            collected.get("amazon", {}).get(category, [])
            if isinstance(collected.get("amazon", {}).get(category, []), list)
            else []
        )
        supply_items = (
            collected.get("1688", {}).get(category, [])
            if isinstance(collected.get("1688", {}).get(category, []), list)
            else []
        )
        for country in countries:
            items = (
                custom_source.get(category, {}).get(country, [])
                if isinstance(custom_source.get(category, {}), dict)
                else []
            )
            if not isinstance(items, list):
                continue
            for item in items[:15]:
                if not isinstance(item, dict):
                    continue
                product = _coerce_product_source(
                    item, category, country, "custom_source"
                )
                if not product:
                    continue
                dedupe_key = (_normalize_name(product["name"]), category, country)
                if dedupe_key in seen:
                    continue
                seen.add(dedupe_key)
                product["matchedAmazon"] = _find_best_match(
                    product["name"], amazon_items, category
                )
                product["matched1688"] = _find_best_match(
                    product["name"], supply_items, category
                )
                products.append(_score_product(product, category_benchmark))

    tiktok_search = collected.get("tiktok", {}).get("search", {})
    for category in categories:
        category_benchmark = benchmarks.get(category, {})
        amazon_items = (
            collected.get("amazon", {}).get(category, [])
            if isinstance(collected.get("amazon", {}).get(category, []), list)
            else []
        )
        supply_items = (
            collected.get("1688", {}).get(category, [])
            if isinstance(collected.get("1688", {}).get(category, []), list)
            else []
        )
        for country in countries:
            items = tiktok_search.get(category, {}).get(country, [])
            if not isinstance(items, list):
                continue

            trend_bonus = min(40, category_benchmark.get("news_count", 0) * 2)
            for item in items[:12]:
                if not isinstance(item, dict):
                    continue
                name = _extract_title(item)
                if not name:
                    continue
                dedupe_key = (_normalize_name(name), category, country)
                if dedupe_key in seen:
                    continue
                seen.add(dedupe_key)

                views = (
                    _to_int(
                        _first_present(
                            item, ["views", "viewCount", "playCount", "plays"]
                        )
                    )
                    or 0
                )
                likes = (
                    _to_int(_first_present(item, ["likes", "likeCount", "diggCount"]))
                    or 0
                )
                comments = (
                    _to_int(_first_present(item, ["comments", "commentCount"])) or 0
                )
                shares = _to_int(_first_present(item, ["shares", "shareCount"])) or 0
                matched_amazon = _find_best_match(name, amazon_items, category)
                matched_1688 = _find_best_match(name, supply_items, category)

                engagement_proxy = likes or max(0, int(views * 0.02))
                search_growth_rate = min(100, int(trend_bonus + min(40, views / 5000)))
                sentiment_score = min(
                    95, max(35, int(50 + min(25, comments / 20) + min(20, shares / 10)))
                )
                price = (
                    _to_float(_first_present(item, ["price", "currentPrice"]))
                    or _to_float(
                        _first_present(
                            matched_amazon or {}, ["price", "currentPrice", "salePrice"]
                        )
                    )
                    or category_benchmark.get("amazon_price")
                    or 0
                )

                source_labels = ["tiktok"]
                if matched_amazon:
                    source_labels.append("amazon")
                if matched_1688:
                    source_labels.append("1688")

                product = {
                    "name": name[:255],
                    "nameEn": name[:255],
                    "category": category,
                    "country": country,
                    "imageUrl": _extract_image(item),
                    "price": round(price, 2) if price else None,
                    "salesVolume": None,
                    "engagementProxy": engagement_proxy,
                    "salesGrowthRate": round(search_growth_rate * 0.6, 1),
                    "sentimentScore": sentiment_score,
                    "searchIndex": _normalize_search_index(search_growth_rate),
                    "searchGrowthRate": search_growth_rate,
                    "tags": _extract_tags(item, category) + source_labels,
                    "salesSource": "tiktok_engagement",
                    "trustLevel": SourceTrust.PROXY.value,
                    "evidenceLinks": _extract_evidence_links(item),
                    "source": "agent:tiktok",
                    "matchedAmazon": matched_amazon,
                    "matched1688": matched_1688,
                }
                products.append(_score_product(product, category_benchmark))

    # 没有 TikTok 结果时，回退到 Amazon 榜单，避免平台没有任何结构化产品。
    if not products:
        for category in categories:
            category_benchmark = benchmarks.get(category, {})
            amazon_items = collected.get("amazon", {}).get(category, [])
            for country in countries[:2]:
                for item in amazon_items[:8]:
                    if not isinstance(item, dict):
                        continue
                    name = _extract_title(item)
                    if not name:
                        continue
                    dedupe_key = (_normalize_name(name), category, country)
                    if dedupe_key in seen:
                        continue
                    seen.add(dedupe_key)

                    review_count = (
                        _to_int(
                            _first_present(
                                item, ["reviewCount", "reviews", "ratingCount"]
                            )
                        )
                        or 0
                    )
                    rating = (
                        _to_float(_first_present(item, ["rating", "score", "stars"]))
                        or 4.0
                    )
                    price = (
                        _to_float(
                            _first_present(item, ["price", "currentPrice", "salePrice"])
                        )
                        or category_benchmark.get("amazon_price")
                        or 0
                    )
                    sentiment_score = min(95, max(40, int(rating * 18)))
                    search_growth_rate = min(
                        100, 20 + category_benchmark.get("news_count", 0) * 3
                    )
                    matched_1688 = _find_best_match(
                        name, collected.get("1688", {}).get(category, []), category
                    )

                    product = {
                        "name": name[:255],
                        "nameEn": name[:255],
                        "category": category,
                        "country": country,
                        "imageUrl": _extract_image(item),
                        "price": round(price, 2) if price else None,
                        "salesVolume": None,
                        "engagementProxy": review_count,
                        "salesGrowthRate": round(search_growth_rate * 0.5, 1),
                        "sentimentScore": sentiment_score,
                        "searchIndex": _normalize_search_index(search_growth_rate),
                        "searchGrowthRate": search_growth_rate,
                        "tags": _extract_tags(item, category)
                        + ["amazon"]
                        + (["1688"] if matched_1688 else []),
                        "salesSource": "amazon_bestsellers",
                        "trustLevel": SourceTrust.PROXY.value,
                        "evidenceLinks": _extract_evidence_links(item),
                        "source": "agent:amazon",
                        "matchedAmazon": item,
                        "matched1688": matched_1688,
                    }
                    products.append(_score_product(product, category_benchmark))

    for product in products:
        product.pop("matchedAmazon", None)
        product.pop("matched1688", None)
        product["tags"] = list(dict.fromkeys(product.get("tags", [])))[:8]
        product["evidenceLinks"] = product.get("evidenceLinks", [])[:3]
        product["whyPicked"] = _generate_why_picked(product)

    products.sort(
        key=lambda item: (item.get("potentialScore", 0), item.get("gmv", 0)),
        reverse=True,
    )
    logger.info(f"    ✅ 候选产品: {len(products)} 条")
    return products[:50]


def _trust_rank(trust_level: str) -> int:
    return {
        SourceTrust.OFFICIAL.value: 0,
        SourceTrust.VERIFIED.value: 1,
        SourceTrust.PROXY.value: 2,
    }.get(trust_level, 3)


def _generate_why_picked(product: dict) -> str:
    bits = []
    trust_level = product.get("trustLevel")
    if trust_level == SourceTrust.OFFICIAL.value and product.get("salesVolume"):
        bits.append(f"真实销量 {int(product['salesVolume']):,} 件")
    elif trust_level == SourceTrust.VERIFIED.value and product.get("salesVolume"):
        bits.append(f"可信来源销量 {int(product['salesVolume']):,} 件")
    elif product.get("engagementProxy"):
        bits.append(f"互动代理 {int(product['engagementProxy']):,}(仅参考)")

    growth = product.get("searchGrowthRate", 0)
    if growth >= HIGH_SEARCH_GROWTH_THRESHOLD:
        bits.append(f"搜索热度增长 +{int(growth)}%")

    competition = product.get("competitionScore", 0)
    if competition >= 70:
        bits.append(f"竞争度偏低(评分 {int(competition)})")

    potential = product.get("potentialScore", 0)
    if potential >= 80:
        bits.append("综合潜力分进入前列")

    sales_source = product.get("salesSource")
    if sales_source and not bits:
        bits.append(f"命中来源 {sales_source}")

    return " | ".join(bits) if bits else "多源交叉命中"


def build_top_picks(
    products: list[dict], limit: int = 10, logger: Optional[logging.Logger] = None
) -> list[dict]:
    ordered = sorted(
        products,
        key=lambda item: (
            _trust_rank(item.get("trustLevel", SourceTrust.PROXY.value)),
            -(item.get("potentialScore", 0)),
        ),
    )
    selected = []
    segment_counts: dict[tuple[str, str], int] = {}
    for product in ordered:
        segment = (product.get("category", ""), product.get("country", ""))
        if segment_counts.get(segment, 0) >= 2:
            continue
        enriched = dict(product)
        enriched["whyPicked"] = _generate_why_picked(enriched)
        selected.append(enriched)
        segment_counts[segment] = segment_counts.get(segment, 0) + 1
        if len(selected) >= limit:
            break

    if logger:
        logger.info("    ✅ Top picks: %s 条", len(selected))
    return selected


# ============================================================
# 阶段五：AI 分析数据包构建
# ============================================================


def build_ai_summary(
    collected: dict,
    products: list,
    categories: list,
    countries: list,
    logger: logging.Logger,
) -> dict:
    """
    构建 AI 分析数据包。
    实际 LLM 调用由平台服务端（invokeLLM）执行，
    本脚本负责准备结构化数据摘要，注入 Prompt 上下文。
    """
    logger.info("  [AI 分析] 构建数据摘要")

    # 提取关键数据点
    data_points = []

    if products:
        top_products = products[:10]
        for product in top_products:
            data_points.append(
                f"候选品 [{product.get('country')}/{product.get('category')}]: "
                f"{product.get('name')} | 潜力 {product.get('potentialScore')} | "
                f"竞争 {product.get('competitionScore')} | 价格 {product.get('price')} | "
                f"热度 {product.get('searchGrowthRate')}"
            )

    # Google Trends 热搜词（结构：{country: [ {title, traffic, date}, ... ]}）
    for country, data in collected.get("google_trends", {}).items():
        if isinstance(data, list) and data:
            kws = [d.get("title", "") for d in data[:5] if isinstance(d, dict)]
            kws = [k for k in kws if k]
            if kws:
                data_points.append(f"Google Trends [{country}]: {', '.join(kws)}")

    # TikTok 探索热点（explore 返回 author/views，search 返回 desc/likes）
    explore = collected.get("tiktok", {}).get("explore")
    if isinstance(explore, list) and explore:
        items = [
            f"{v.get('author', '?')}({v.get('views', '?')})"
            for v in explore[:5]
            if isinstance(v, dict)
        ]
        if items:
            data_points.append(f"TikTok Explore 热门: {', '.join(items)}")

    # 1688 供货价
    for cat, data in collected.get("1688", {}).items():
        if isinstance(data, list) and data:
            items = [d.get("title", "")[:25] for d in data[:3] if isinstance(d, dict)]
            items = [i for i in items if i]
            if items:
                data_points.append(f"1688 [{cat}]: {', '.join(items)}")

    # 小红书
    for cat, data in collected.get("xiaohongshu", {}).items():
        if isinstance(data, list) and data:
            titles = [d.get("title", "")[:30] for d in data[:3] if isinstance(d, dict)]
            titles = [t for t in titles if t]
            if titles:
                data_points.append(f"小红书 [{cat}]: {', '.join(titles)}")

    # Reddit 情绪
    for cat, data in collected.get("reddit", {}).items():
        if isinstance(data, list) and data:
            titles = [p.get("title", "")[:40] for p in data[:2] if isinstance(p, dict)]
            data_points.append(f"Reddit [{cat}]: {', '.join(titles)}")

    summary_text = (
        "\n".join(data_points) if data_points else "（数据采集中，部分数据源需要登录）"
    )

    return {
        "status": "ready_for_llm",
        "categories": categories,
        "countries": [COUNTRY_NAMES.get(c, c) for c in countries],
        "data_summary": summary_text,
        "data_sources_used": list(collected.keys()),
        "candidate_products": len(products),
        "collection_time": datetime.now().isoformat(),
        "llm_prompt_template": (
            "你是 TikTok 东南亚跨境电商选品顾问。基于以下真实市场数据，"
            f"为目标国家 {', '.join(COUNTRY_NAMES.get(c, c) for c in countries)} 的 "
            f"{', '.join(categories)} 品类生成选品建议：\n\n"
            f"{summary_text}\n\n"
            "请输出：1) 推荐爆款产品列表（含潜力评分）"
            "2) 市场情绪判断 3) 入场时机建议 4) 风险提示"
        ),
    }


# ============================================================
# 数据上报到平台
# ============================================================


def write_to_platform(
    run_record: dict, platform_url: str, logger: logging.Logger
) -> bool:
    """将运行记录写入平台（通过 tRPC dataSync.recordRun API）"""
    try:
        import urllib.request

        token = os.environ.get("PLATFORM_SERVICE_TOKEN")
        payload = json.dumps(
            {
                "json": {
                    "runId": run_record["run_id"],
                    "mode": run_record["mode"],
                    "status": run_record["status"],
                    "categories": run_record.get("categories", []),
                    "countries": run_record.get("countries", []),
                    "summary": run_record.get("summary", {}),
                    "products": run_record.get("products", []),
                    "topPicks": run_record.get("top_picks", []),
                }
            }
        ).encode()

        headers = {"Content-Type": "application/json"}
        if token:
            headers["Authorization"] = f"Bearer {token}"

        req = urllib.request.Request(
            f"{platform_url.rstrip('/')}/api/trpc/dataSync.recordRun",
            data=payload,
            headers=headers,
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            if resp.status == 200:
                logger.info("  ✅ 运行记录已写入平台数据库")
                return True
    except Exception as e:
        run_record["status"] = "degraded"
        run_record.setdefault("summary", {})["platform_write_status"] = "degraded"
        logger.warning(f"  ⚠️  平台写入失败: {e}")
        logger.warning("     → 数据已保存到本地文件，可手动同步")
    return False


# ============================================================
# 主 Agent 入口
# ============================================================


def run_agent(
    mode: str = "standard",
    categories: list = None,
    countries: list = None,
    platform_url: str = "http://localhost:3000",
    write_db: bool = False,
    skip_preflight: bool = False,
) -> dict:
    """
    Agent 主入口。由 Manus schedule 工具或命令行触发。

    模式说明：
      quick    — Google Trends + Google News（无需任何登录，约 3 分钟）
      standard — 上述 + TikTok 搜索/探索（需要 Chrome 登录，约 8 分钟）
      deep     — 全部数据源（含 Amazon / 1688 / Reddit / 小红书，约 20 分钟）

    Returns:
        {"status": "success"|"error", "run_id": str, "summary": dict}
    """
    run_id = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    logger = setup_logging(run_id)
    categories = categories or DEFAULT_CATEGORIES
    countries = countries or DEFAULT_COUNTRIES
    started_at = datetime.now().isoformat()

    logger.info("=" * 60)
    logger.info("🚀 TikTok 东南亚选品 Agent 启动")
    logger.info(f"   运行 ID : {run_id}")
    logger.info(f"   模式    : {mode.upper()}")
    logger.info(f"   品类    : {', '.join(categories)}")
    logger.info(f"   国家    : {', '.join(countries)}")
    logger.info(f"   平台    : {platform_url}")
    logger.info("=" * 60)

    # 启动自检
    preflight = run_preflight_check(mode, logger, skip_preflight=skip_preflight)
    has_opencli_bridge = preflight.get("bridge", False)

    collected: dict = {}

    try:
        # ── 阶段一：公开数据（所有模式必跑）──────────────────────
        logger.info("── 阶段一：公开数据采集（OpenCLI，无需登录）──")
        collected["google_trends"] = collect_google_trends(
            categories, countries, logger
        )
        collected["google_news"] = collect_google_news(categories, countries, logger)

        # ── 阶段二：OpenCLI 需 Browser Bridge 的数据源 ──────────
        if mode in ("standard", "deep"):
            logger.info("── 阶段二：OpenCLI 登录数据采集 ──")
            collected["custom_source"] = collect_custom_source(
                categories, countries, logger
            )
            if has_opencli_bridge:
                collected["tiktok"] = collect_tiktok(categories, countries, logger)
                if mode == "deep":
                    collected["amazon"] = collect_amazon(categories, logger)
                    collected["reddit"] = collect_reddit(categories, logger)
                    collected["xiaohongshu"] = collect_xiaohongshu(categories, logger)
            else:
                logger.warning(
                    "  ⚠️  跳过 TikTok/Amazon/Reddit（Browser Bridge 未连接）"
                )
                logger.warning("     → 安装 OpenCLI Chrome 扩展后重新运行")

        # ── 阶段三：1688 供货价 ─────────────────────────────────
        if mode == "deep":
            logger.info("── 阶段三：1688 供货价 ──")
            if has_opencli_bridge:
                collected["1688"] = collect_1688(categories, logger)

        # ── 阶段四：结构化候选产品与评分 ────────────────────────
        logger.info("── 阶段四：候选产品结构化与评分 ──")
        products = build_structured_products(collected, categories, countries, logger)
        top_picks = build_top_picks(products, logger=logger)

        # ── 阶段五：构建 AI 分析数据包 ─────────────────────────
        logger.info("── 阶段五：AI 分析数据包构建 ──")
        collected["ai_summary"] = build_ai_summary(
            collected, products, categories, countries, logger
        )

        # ── 统计摘要 ─────────────────────────────────────────────
        output_file = DATA_DIR / f"run_{run_id}.json"
        summary = {
            "google_trends_countries": len(collected.get("google_trends", {})),
            "custom_source_categories": len(collected.get("custom_source", {})),
            "tiktok_categories": len(collected.get("tiktok", {}).get("search", {})),
            "amazon_categories": len(collected.get("amazon", {})),
            "1688_categories": len(collected.get("1688", {})),
            "reddit_categories": len(collected.get("reddit", {})),
            "xiaohongshu_categories": len(collected.get("xiaohongshu", {})),
            "candidate_products": len(products),
            "top_picks": top_picks,
            "top_potential_score": products[0].get("potentialScore", 0)
            if products
            else 0,
            "output_file": str(output_file),
        }

        run_record = {
            "run_id": run_id,
            "mode": mode,
            "categories": categories,
            "countries": countries,
            "started_at": started_at,
            "completed_at": datetime.now().isoformat(),
            "status": "success",
            "tools_used": {
                "opencli_bridge": has_opencli_bridge,
            },
            "summary": summary,
            "products": products,
            "top_picks": top_picks,
            "data": collected,
        }
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(run_record, f, ensure_ascii=False, indent=2)
        logger.info(f"✅ 数据已保存: {output_file}")

        # ── 写入平台 ─────────────────────────────────────────────
        if write_db:
            write_to_platform(run_record, platform_url, logger)

        logger.info("=" * 60)
        logger.info("✅ Agent 运行完成")
        logger.info(f"   Google Trends  : {summary['google_trends_countries']} 个国家")
        logger.info(f"   Custom Source  : {summary['custom_source_categories']} 个品类")
        logger.info(f"   TikTok 品类    : {summary['tiktok_categories']} 个")
        logger.info(f"   Amazon 品类    : {summary['amazon_categories']} 个")
        logger.info(f"   1688 品类      : {summary['1688_categories']} 个")
        logger.info(f"   Reddit 品类    : {summary['reddit_categories']} 个")
        logger.info(f"   小红书 品类    : {summary['xiaohongshu_categories']} 个")
        logger.info(f"   候选产品       : {summary['candidate_products']} 个")
        logger.info(f"   Top Picks      : {len(top_picks)} 个")
        logger.info(f"   输出文件       : {summary['output_file']}")
        logger.info("=" * 60)

        return {"status": "success", "run_id": run_id, "summary": summary}

    except Exception as e:
        logger.error(f"❌ Agent 运行失败: {e}", exc_info=True)
        return {"status": "error", "run_id": run_id, "error": str(e)}


# ============================================================
# CLI 入口
# ============================================================

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="TikTok 东南亚选品 Agent — 可调度自动化数据采集",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
工具链：
  OpenCLI — 公开数据 + 需登录的结构化平台数据（通过 Browser Bridge Chrome 扩展连接本机 Chrome）

依赖安装：
  npm install -g @jackwener/opencli

示例:
  # 快速模式（仅 Google Trends/News，无需登录，约 3 分钟）
  python sea_product_agent.py --mode quick

  # 标准模式（含 TikTok，约 8 分钟）
  python sea_product_agent.py --mode standard --write-db --platform-url https://your-platform.manus.space

  # 深度模式（全量数据源，约 20 分钟）
  python sea_product_agent.py --mode deep --categories beauty,fashion --countries ID,TH,VN

调度（通过 Manus schedule 工具设置）:
  每日 08:00 快速更新: cron "0 0 8 * * *"
  每日 20:00 标准采集: cron "0 0 20 * * *"
  每周一深度分析:      cron "0 0 6 * * 1"
        """,
    )
    parser.add_argument(
        "--mode",
        choices=["quick", "standard", "deep"],
        default="standard",
        help="运行模式 (默认: standard)",
    )
    parser.add_argument(
        "--categories",
        default=",".join(DEFAULT_CATEGORIES),
        help="品类列表，逗号分隔 (默认: beauty,fashion,home,electronics,health)",
    )
    parser.add_argument(
        "--countries",
        default=",".join(DEFAULT_COUNTRIES),
        help="国家列表，逗号分隔 (默认: ID,TH,VN,PH,MY)",
    )
    parser.add_argument(
        "--platform-url",
        default=os.environ.get("SEA_PLATFORM_URL", "http://localhost:3000"),
        help="选品平台 URL (默认: http://localhost:3000 或 $SEA_PLATFORM_URL)",
    )
    parser.add_argument(
        "--write-db",
        action="store_true",
        help="将运行记录写入平台数据库",
    )
    parser.add_argument(
        "--skip-preflight",
        action="store_true",
        help="跳过启动自检；适合已知本机环境稳定时减少真实探测请求",
    )

    args = parser.parse_args()
    result = run_agent(
        mode=args.mode,
        categories=[c.strip() for c in args.categories.split(",") if c.strip()],
        countries=[c.strip().upper() for c in args.countries.split(",") if c.strip()],
        platform_url=args.platform_url,
        write_db=args.write_db,
        skip_preflight=args.skip_preflight,
    )

    sys.exit(0 if result["status"] == "success" else 1)
