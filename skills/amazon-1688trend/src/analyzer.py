"""趋势分析引擎 - 报告生成和导出 (by HomeSafe)"""

import csv
import json
import logging
from datetime import date

from src.database import Database

logger = logging.getLogger(__name__)


class TrendReport:
    """趋势报告生成器"""

    def __init__(self, db: Database):
        self.db = db

    def generate(self, platform: str, days: int = 7,
                 limit: int = 20, rising_only: bool = False) -> str:
        """生成可读的趋势报告文本"""
        trending = self.db.get_trending(platform, days, limit, rising_only)
        if not trending:
            return f"\n  📭 [{platform}] 近 {days} 天没有采集到关键词数据。请先运行 collect 命令。\n"

        lines = []
        lines.append(f"\n{'='*60}")
        lines.append(f"  📊 {platform.upper()} 热词趋势报告 (近 {days} 天)")
        lines.append(f"{'='*60}")
        lines.append(f"{'#':>3} {'关键词':<28} {'热度':>6} {'变化率':>8} {'来源':<14} {'新词':<4}")
        lines.append(f"{'─'*60}")
        lines.append(f"{'─'*60}")

        for i, item in enumerate(trending, 1):
            kw = item['keyword'][:28]
            freq = item['current_freq']
            change = item['change_pct']
            source = item['source'][:14]
            is_new = "🆕" if item['is_new'] else ""

            # 变化率指示器
            if change > 50:
                trend_icon = " 🔥"
            elif change > 20:
                trend_icon = " ↑"
            elif change < -20:
                trend_icon = " ↓"
            else:
                trend_icon = " →"

            change_str = f"{change:+.1f}%{trend_icon}"
            lines.append(f"{i:>3} {kw:<28} {freq:>6} {change_str:>14} {source:<14} {is_new:<4}")

        lines.append(f"{'─'*60}")
        lines.append(f"  共 {len(trending)} 个热词")
        lines.append(f"  🔥 变化率 >+50%  ↑ 变化率 >+20%  → 平稳  ↓ 下降 >20%")
        lines.append(f"  🆕 新词（首次出现在近 {days} 天内）")
        lines.append(f"\n  提示: 用 --rising 只看升温词, 用 --days 调整时间范围\n")
        return "\n".join(lines)

    def export_csv(self, platform: str, days: int, output_path: str):
        """导出为 CSV 文件"""
        data = self.db.get_raw_data(platform, days)
        if not data:
            logger.warning(f"没有数据可导出 ({platform}, {days}天)")
            return

        with open(output_path, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.DictWriter(f, fieldnames=['keyword', 'platform', 'source', 'date', 'frequency', 'rank'])
            writer.writeheader()
            writer.writerows(data)
        logger.info(f"已导出 CSV: {output_path}")

    def export_json(self, platform: str, days: int, output_path: str):
        """导出为 JSON 文件"""
        data = self.db.get_raw_data(platform, days)
        if not data:
            logger.warning(f"没有数据可导出 ({platform}, {days}天)")
            return

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        logger.info(f"已导出 JSON: {output_path}")
