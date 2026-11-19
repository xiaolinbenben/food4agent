"""定时调度器 - 周期性自动采集 (by HomeSafe)"""

import time
import signal
import logging
from datetime import datetime

import schedule

from src.database import Database
from src.collector_1688 import Collector1688
from src.collector_amazon import CollectorAmazon

logger = logging.getLogger(__name__)


class Scheduler:
    """定时采集调度器"""

    def __init__(self, config: dict, db: Database):
        self.config = config
        self.db = db
        self._running = False
        self._collectors = {
            '1688': Collector1688(config, db),
            'amazon': CollectorAmazon(config, db),
        }

    def _collect_all(self):
        """执行全平台采集"""
        logger.info("=" * 50)
        logger.info(f"🕐 定时采集开始: {datetime.now().isoformat()}")
        logger.info("=" * 50)
        for name, collector in self._collectors.items():
            enabled = self.config.get(name, {}).get('enabled', True)
            if not enabled:
                logger.info(f"[{name}] 已禁用，跳过")
                continue
            try:
                count = collector.run_and_store()
                logger.info(f"[{name}] ✅ 采集完成，新增/更新 {count} 个词")
            except Exception as e:
                logger.error(f"[{name}] ❌ 采集失败: {e}")

    def start(self, interval_hours: int = None):
        """启动定时循环"""
        if interval_hours is None:
            interval_hours = self.config.get('collector', {}).get('interval_hours', 6)

        interval_str = f"每 {interval_hours} 小时"
        logger.info(f"📅 启动定时采集: {interval_str}")
        logger.info("  按 Ctrl+C 停止")

        # 启动时立即执行一次
        self._collect_all()

        # 设定时任务
        schedule.every(interval_hours).hours.do(self._collect_all)

        # 信号处理
        self._running = True
        signal.signal(signal.SIGINT, self._stop)
        signal.signal(signal.SIGTERM, self._stop)

        while self._running:
            schedule.run_pending()
            time.sleep(30)

        logger.info("⏹ 定时采集已停止")

    def _stop(self, signum, frame):
        self._running = False
        logger.info("收到停止信号，正在退出...")
