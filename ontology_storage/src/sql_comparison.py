"""
关系型存储 vs 本体论存储 对比实现

同一批数据，用 SQLite（关系模型）和 RDF 图（本体论模型）分别存储，
对比在扩展新关系、跨实体查询、类型推断三个维度的差异。
"""
from __future__ import annotations

import sqlite3
import time
from typing import Any


# ─────────────────────────────────────────────────────────────────────────────
# 关系型存储实现
# ─────────────────────────────────────────────────────────────────────────────

SQL_SCHEMA = """
CREATE TABLE IF NOT EXISTS technologies (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT UNIQUE NOT NULL,
    type        TEXT NOT NULL,  -- 'PLang' | 'MLFramework' | 'WebFramework' | 'Database'
    release_year INTEGER,
    license     TEXT,
    github_stars INTEGER,
    description TEXT
);

CREATE TABLE IF NOT EXISTS organizations (
    id   INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL
);

CREATE TABLE IF NOT EXISTS tech_created_by (
    tech_id  INTEGER REFERENCES technologies(id),
    org_id   INTEGER REFERENCES organizations(id),
    PRIMARY KEY (tech_id, org_id)
);

-- 技术间关系需要为每种关系建单独表
CREATE TABLE IF NOT EXISTS tech_used_with (
    tech_a INTEGER REFERENCES technologies(id),
    tech_b INTEGER REFERENCES technologies(id),
    PRIMARY KEY (tech_a, tech_b)
);

CREATE TABLE IF NOT EXISTS tech_built_on (
    child  INTEGER REFERENCES technologies(id),
    parent INTEGER REFERENCES technologies(id),
    PRIMARY KEY (child, parent)
);

CREATE TABLE IF NOT EXISTS tech_competitor (
    tech_a INTEGER REFERENCES technologies(id),
    tech_b INTEGER REFERENCES technologies(id),
    PRIMARY KEY (tech_a, tech_b)
);
"""

SAMPLE_DATA_SQL = [
    # technologies
    ("INSERT OR IGNORE INTO technologies (name,type,release_year,license,github_stars,description) VALUES (?,?,?,?,?,?)", [
        ("Python",      "PLang",       1991, "PSF-2.0",       None,   "通用高级语言，AI/ML 领域事实标准"),
        ("PyTorch",     "MLFramework", 2016, "BSD-3-Clause",  82000,  "动态计算图深度学习框架"),
        ("TensorFlow",  "MLFramework", 2015, "Apache-2.0",    185000, "Google 开源深度学习框架"),
        ("Transformers","MLFramework", 2018, "Apache-2.0",    130000, "预训练 NLP 模型库"),
        ("FastAPI",     "WebFramework",2018, "MIT",           75000,  "高性能异步 Python Web 框架"),
        ("Milvus",      "Database",    2019, "Apache-2.0",    30000,  "开源向量数据库"),
        ("Neo4j",       "Database",    2007, "GPL-3.0",       None,   "主流图数据库"),
        ("PostgreSQL",  "Database",    1996, "PostgreSQL",    None,   "开源关系型数据库"),
        ("ChromaDB",    "Database",    2022, "Apache-2.0",    None,   "轻量嵌入式向量数据库"),
    ]),
]


class SQLStorage:
    def __init__(self, db_path: str = ":memory:"):
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self._init_schema()
        self._load_sample()

    def _init_schema(self):
        self.conn.executescript(SQL_SCHEMA)

    def _load_sample(self):
        cur = self.conn.cursor()
        for stmt, rows in SAMPLE_DATA_SQL:
            for row in rows:
                cur.execute(stmt, row)
        # 关系数据
        relations = [
            # usedWith（需要双向插入以保持对称）
            ("Python",       "PyTorch",      "used_with"),
            ("PyTorch",      "Python",       "used_with"),
            ("Python",       "FastAPI",      "used_with"),
            ("FastAPI",      "Python",       "used_with"),
            ("PyTorch",      "Milvus",       "used_with"),
            ("Milvus",       "PyTorch",      "used_with"),
            # builtOn
            ("Transformers", "PyTorch",      "built_on"),
            ("Transformers", "TensorFlow",   "built_on"),
            # competitorOf（同样需双向）
            ("PyTorch",      "TensorFlow",   "competitor"),
            ("TensorFlow",   "PyTorch",      "competitor"),
            ("Milvus",       "ChromaDB",     "competitor"),
            ("ChromaDB",     "Milvus",       "competitor"),
        ]
        for a, b, rel in relations:
            a_id = cur.execute("SELECT id FROM technologies WHERE name=?", (a,)).fetchone()
            b_id = cur.execute("SELECT id FROM technologies WHERE name=?", (b,)).fetchone()
            if not a_id or not b_id:
                continue
            if rel == "used_with":
                cur.execute("INSERT OR IGNORE INTO tech_used_with VALUES (?,?)", (a_id[0], b_id[0]))
            elif rel == "built_on":
                cur.execute("INSERT OR IGNORE INTO tech_built_on VALUES (?,?)", (a_id[0], b_id[0]))
            elif rel == "competitor":
                cur.execute("INSERT OR IGNORE INTO tech_competitor VALUES (?,?)", (a_id[0], b_id[0]))
        self.conn.commit()

    def query_ml_frameworks(self) -> list[dict]:
        """查询所有 MLFramework"""
        rows = self.conn.execute(
            "SELECT name, github_stars, release_year FROM technologies "
            "WHERE type='MLFramework' ORDER BY github_stars DESC"
        ).fetchall()
        return [dict(r) for r in rows]

    def query_python_ecosystem(self) -> list[dict]:
        """查询与 Python usedWith 的技术（SQL 中无法自动推断反向）"""
        rows = self.conn.execute("""
            SELECT t2.name, t2.type
            FROM technologies t1
            JOIN tech_used_with uw ON t1.id = uw.tech_a
            JOIN technologies t2 ON uw.tech_b = t2.id
            WHERE t1.name = 'Python'
        """).fetchall()
        return [dict(r) for r in rows]

    def add_new_relation_type(self):
        """
        演示：在 SQL 中添加新关系类型（如 recommendedFor）需要 DDL ALTER TABLE
        在 RDF 中只需直接插入新三元组，无需更改 schema
        """
        try:
            self.conn.execute(
                "CREATE TABLE tech_recommended_for ("
                "  tech_id INTEGER, context TEXT, PRIMARY KEY(tech_id, context)"
                ")"
            )
            return "需要 CREATE TABLE DDL 操作"
        except sqlite3.OperationalError as e:
            return f"DDL 失败: {e}"

    def stats(self) -> dict:
        cur = self.conn.cursor()
        return {
            "technologies": cur.execute("SELECT COUNT(*) FROM technologies").fetchone()[0],
            "used_with_pairs": cur.execute("SELECT COUNT(*) FROM tech_used_with").fetchone()[0],
            "built_on_pairs": cur.execute("SELECT COUNT(*) FROM tech_built_on").fetchone()[0],
        }
