"""数据库模块 - SQLite 存储和查询 (by HomeSafe)"""

import sqlite3
import json
import os
from datetime import datetime, date, timedelta

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS keywords (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    platform TEXT NOT NULL,
    keyword TEXT NOT NULL,
    source TEXT NOT NULL DEFAULT 'unknown',
    first_seen TEXT NOT NULL,
    last_seen TEXT NOT NULL,
    UNIQUE(platform, keyword)
);

CREATE TABLE IF NOT EXISTS daily_stats (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    keyword_id INTEGER NOT NULL,
    date TEXT NOT NULL,
    rank INTEGER DEFAULT NULL,
    frequency INTEGER DEFAULT 1,
    meta TEXT DEFAULT '{}',
    FOREIGN KEY (keyword_id) REFERENCES keywords(id),
    UNIQUE(keyword_id, date)
);

CREATE TABLE IF NOT EXISTS collection_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    platform TEXT NOT NULL,
    started_at TEXT NOT NULL,
    finished_at TEXT DEFAULT NULL,
    keywords_found INTEGER DEFAULT 0,
    status TEXT DEFAULT 'running'
);

CREATE INDEX IF NOT EXISTS idx_keywords_platform ON keywords(platform);
CREATE INDEX IF NOT EXISTS idx_daily_stats_date ON daily_stats(date);
CREATE INDEX IF NOT EXISTS idx_daily_stats_keyword ON daily_stats(keyword_id);
CREATE INDEX IF NOT EXISTS idx_collection_log_platform ON collection_log(platform);
"""


class Database:
    def __init__(self, db_path: str):
        os.makedirs(os.path.dirname(db_path) or '.', exist_ok=True)
        self.db_path = db_path
        self._conn = sqlite3.connect(db_path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._init_schema()

    def _init_schema(self):
        for stmt in SCHEMA_SQL.split(';'):
            stmt = stmt.strip()
            if stmt:
                self._conn.execute(stmt)
        self._conn.commit()

    def ensure_keyword(self, platform: str, keyword: str, source: str) -> int:
        """返回 keyword_id，不存在则创建"""
        now = datetime.utcnow().isoformat()
        cur = self._conn.execute(
            "INSERT OR IGNORE INTO keywords (platform, keyword, source, first_seen, last_seen) "
            "VALUES (?, ?, ?, ?, ?)",
            (platform, keyword.strip().lower(), source, now, now)
        )
        if cur.rowcount == 0:
            # 已存在，更新 last_seen
            self._conn.execute(
                "UPDATE keywords SET last_seen = ?, source = ? WHERE platform = ? AND keyword = ?",
                (now, source, platform, keyword.strip().lower())
            )
        row = self._conn.execute(
            "SELECT id FROM keywords WHERE platform = ? AND keyword = ?",
            (platform, keyword.strip().lower())
        ).fetchone()
        self._conn.commit()
        return row['id']

    def record_daily_stat(self, keyword_id: int, stat_date: str = None,
                          rank: int = None, frequency: int = 1, meta: dict = None):
        """记录关键词某天的数据"""
        if stat_date is None:
            stat_date = date.today().isoformat()
        meta_json = json.dumps(meta or {}, ensure_ascii=False)
        self._conn.execute(
            "INSERT OR IGNORE INTO daily_stats (keyword_id, date, rank, frequency, meta) "
            "VALUES (?, ?, ?, ?, ?)",
            (keyword_id, stat_date, rank, frequency, meta_json)
        )
        self._conn.commit()

    def start_collection_log(self, platform: str) -> int:
        now = datetime.utcnow().isoformat()
        cur = self._conn.execute(
            "INSERT INTO collection_log (platform, started_at, status) VALUES (?, ?, 'running')",
            (platform, now)
        )
        self._conn.commit()
        return cur.lastrowid

    def finish_collection_log(self, log_id: int, keywords_found: int, status: str = 'success'):
        now = datetime.utcnow().isoformat()
        self._conn.execute(
            "UPDATE collection_log SET finished_at = ?, keywords_found = ?, status = ? WHERE id = ?",
            (now, keywords_found, status, log_id)
        )
        self._conn.commit()

    def get_keywords_by_platform(self, platform: str, limit: int = 100):
        rows = self._conn.execute(
            "SELECT * FROM keywords WHERE platform = ? ORDER BY last_seen DESC LIMIT ?",
            (platform, limit)
        ).fetchall()
        return [dict(r) for r in rows]

    def get_trending(self, platform: str, days: int = 7, limit: int = 20, rising_only: bool = False):
        """获取趋势热词
        返回: [(keyword, current_freq, previous_freq, change_pct, first_seen, source), ...]
        """
        today = date.today()
        current_start = (today - timedelta(days=days)).isoformat()
        current_end = today.isoformat()
        previous_start = (today - timedelta(days=days * 2)).isoformat()
        previous_end = (today - timedelta(days=days)).isoformat()

        rows = self._conn.execute("""
            SELECT k.keyword, k.source, k.first_seen,
                   COALESCE(curr.cnt, 0) AS current_freq,
                   COALESCE(prev.cnt, 0) AS previous_freq
            FROM keywords k
            LEFT JOIN (
                SELECT keyword_id, SUM(frequency) AS cnt
                FROM daily_stats
                WHERE date >= ? AND date <= ?
                GROUP BY keyword_id
            ) curr ON curr.keyword_id = k.id
            LEFT JOIN (
                SELECT keyword_id, SUM(frequency) AS cnt
                FROM daily_stats
                WHERE date >= ? AND date < ?
                GROUP BY keyword_id
            ) prev ON prev.keyword_id = k.id
            WHERE k.platform = ?
              AND (curr.cnt > 0 OR prev.cnt > 0)
            ORDER BY curr.cnt DESC
        """, (current_start, current_end, previous_start, previous_end, platform))

        results = []
        for r in rows.fetchall():
            cf = r['current_freq'] or 0
            pf = r['previous_freq'] or 0
            change_pct = ((cf - pf) / pf * 100) if pf > 0 else (100 if cf > 0 else 0)

            entry = {
                'keyword': r['keyword'],
                'source': r['source'],
                'first_seen': r['first_seen'],
                'current_freq': cf,
                'previous_freq': pf,
                'change_pct': round(change_pct, 1),
                'is_new': r['first_seen'] >= current_start
            }
            results.append(entry)

        if rising_only:
            results = [r for r in results if r['change_pct'] > 0]

        # 排序：新词优先，然后按变化率降序
        results.sort(key=lambda x: (not x['is_new'], -x['change_pct'], -x['current_freq']))

        return results[:limit]

    def get_raw_data(self, platform: str, days: int = 7):
        """导出原始数据"""
        start = (date.today() - timedelta(days=days)).isoformat()
        rows = self._conn.execute("""
            SELECT k.keyword, k.platform, k.source, ds.date, ds.frequency, ds.rank
            FROM daily_stats ds
            JOIN keywords k ON k.id = ds.keyword_id
            WHERE k.platform = ? AND ds.date >= ?
            ORDER BY ds.date DESC, ds.frequency DESC
        """, (platform, start))
        return [dict(r) for r in rows.fetchall()]

    def close(self):
        self._conn.close()
