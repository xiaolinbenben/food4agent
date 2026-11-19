#!/usr/bin/env python3
"""Amazon & 1688 跨境电商热词趋势追踪 - CLI 入口 (by HomeSafe)"""

import os
import sys
import json
import argparse
import logging
import secrets
from datetime import datetime

# 将项目根目录加入 sys.path
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_ROOT)

from src.database import Database
from src.collector_1688 import Collector1688
from src.collector_amazon import CollectorAmazon
from src.analyzer import TrendReport
from src.scheduler import Scheduler

# ── 配置加载 ──────────────────────────────────────────

def load_config() -> dict:
    config_path = os.path.join(PROJECT_ROOT, 'config.json')
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)

    # secret_key 自动生成
    if not config.get('secret_key'):
        config['secret_key'] = secrets.token_hex(32)
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)

    # 环境变量覆盖
    config['data_dir'] = os.path.expanduser(
        os.environ.get('TRENDS_DATA_DIR', config.get('data_dir', 'data'))
    )

    return config


# ── 自动获取 IP ───────────────────────────────────────

def get_server_ip() -> str:
    try:
        import urllib.request
        req = urllib.request.Request(
            "http://ip-api.com/json/?fields=query",
            headers={"User-Agent": "curl/8.0"}
        )
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read())
            return data.get("query", "0.0.0.0")
    except Exception:
        pass
    try:
        import socket
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(0.1)
        s.connect(("8.8.8.8", 80))
        ip = s.sockname[0]
        s.close()
        return ip
    except Exception:
        return "0.0.0.0"


# ── 日志配置 ──────────────────────────────────────────

def setup_logging(level: str = 'INFO'):
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format='%(asctime)s [%(levelname)s] %(message)s',
        datefmt='%H:%M:%S'
    )


# ── CLI 命令 ──────────────────────────────────────────

def cmd_collect(args, config, db):
    """手动采集热词数据"""
    platform = args.platform
    collectors = {}

    if platform in ('1688', 'all'):
        collectors['1688'] = Collector1688(config, db)
    if platform in ('amazon', 'all'):
        collectors['amazon'] = CollectorAmazon(config, db)

    for name, collector in collectors.items():
        print(f"\n  🔄 采集 [{name}] 热词...")
        try:
            count = collector.run_and_store()
            print(f"  ✅ [{name}] 完成: 发现 {count} 个关键词")
        except Exception as e:
            print(f"  ❌ [{name}] 失败: {e}")


def cmd_report(args, config, db):
    """生成趋势报告"""
    report = TrendReport(db)
    platforms = ['1688', 'amazon'] if args.platform == 'all' else [args.platform]
    for p in platforms:
        text = report.generate(p, args.days, args.limit, args.rising)
        print(text)


def cmd_export(args, config, db):
    """导出数据"""
    report = TrendReport(db)
    platforms = ['1688', 'amazon'] if args.platform == 'all' else [args.platform]

    for p in platforms:
        output = args.output or f"trends_{p}_{datetime.now().strftime('%Y%m%d')}.{args.format}"
        if args.format == 'csv':
            report.export_csv(p, args.days, output)
        else:
            report.export_json(p, args.days, output)
        print(f"  ✅ 已导出: {output}")


def cmd_schedule(args, config, db):
    """启动定时采集"""
    scheduler = Scheduler(config, db)
    scheduler.start(args.interval)


# ── 启动 Banner ───────────────────────────────────────

def print_banner(config):
    server_ip = get_server_ip()
    port = config.get('port', 8080)  # 占位，暂无 web 服务

    print(f"  ╔═══════════════════════════════════════════╗")
    print(f"  ║   Amazon & 1688 热词趋势追踪 v1.0         ║")
    print(f"  ║   by HomeSafe                              ║")
    print(f"  ╚═══════════════════════════════════════════╝")
    print(f"  📡 服务器: {server_ip}:{port}")
    print(f"  🗄️  数据库: {config['database']}")
    print(f"  🔑 Secret: {config['secret_key'][:8]}...")
    print()


# ── 主入口 ────────────────────────────────────────────

def main():
    config = load_config()
    setup_logging(config.get('log_level', 'INFO'))

    db_path = os.path.join(PROJECT_ROOT, config['database'])
    db = Database(db_path)

    parser = argparse.ArgumentParser(
        description='Amazon & 1688 跨境电商热词趋势追踪 (by HomeSafe)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python main.py collect --all
  python main.py collect --platform 1688
  python main.py report --days 7 --platform amazon --rising
  python main.py report --days 14 --limit 30
  python main.py export --format csv --days 7
  python main.py schedule --interval 6
        """
    )

    subparsers = parser.add_subparsers(dest='command', help='命令')

    # collect
    p_collect = subparsers.add_parser('collect', help='手动采集热词数据')
    p_collect.add_argument('--platform', choices=['1688', 'amazon', 'all'],
                           default='all', help='采集平台 (默认: all)')

    # report
    p_report = subparsers.add_parser('report', help='生成趋势报告')
    p_report.add_argument('--days', type=int, default=7, help='分析近 N 天趋势 (默认: 7)')
    p_report.add_argument('--platform', choices=['1688', 'amazon', 'all'],
                          default='all', help='平台筛选 (默认: all)')
    p_report.add_argument('--limit', type=int, default=20, help='显示前 N 个热词 (默认: 20)')
    p_report.add_argument('--rising', action='store_true', help='只显示升温词')

    # export
    p_export = subparsers.add_parser('export', help='导出数据')
    p_export.add_argument('--format', choices=['csv', 'json'], default='csv', help='导出格式')
    p_export.add_argument('--days', type=int, default=7, help='导出近 N 天数据 (默认: 7)')
    p_export.add_argument('--platform', choices=['1688', 'amazon', 'all'],
                          default='all', help='平台筛选 (默认: all)')
    p_export.add_argument('--output', type=str, default=None, help='输出文件路径')

    # schedule
    p_sched = subparsers.add_parser('schedule', help='启动定时采集')
    p_sched.add_argument('--interval', type=int, default=None,
                         help='采集间隔(小时) (默认: config.json 中的值)')

    args = parser.parse_args()

    print_banner(config)

    if args.command == 'collect':
        cmd_collect(args, config, db)
    elif args.command == 'report':
        cmd_report(args, config, db)
    elif args.command == 'export':
        cmd_export(args, config, db)
    elif args.command == 'schedule':
        cmd_schedule(args, config, db)
    else:
        parser.print_help()

    db.close()


if __name__ == '__main__':
    main()
