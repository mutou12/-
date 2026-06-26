import sqlite3
from pathlib import Path
from typing import List, Tuple

from ontology_storage.ontology import CLASSES, PROPERTIES, TRIPLES


def get_connection(db_path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def init_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS ontology_classes (
            name TEXT PRIMARY KEY,
            description TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS ontology_properties (
            name TEXT PRIMARY KEY,
            domain_name TEXT NOT NULL,
            range_type TEXT NOT NULL,
            description TEXT NOT NULL,
            FOREIGN KEY(domain_name) REFERENCES ontology_classes(name)
        );

        CREATE TABLE IF NOT EXISTS triples (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            subject TEXT NOT NULL,
            predicate TEXT NOT NULL,
            object_value TEXT NOT NULL
        );
        """
    )


def seed_ontology(conn: sqlite3.Connection) -> None:
    conn.executemany(
        """
        INSERT OR REPLACE INTO ontology_classes(name, description)
        VALUES(?, ?)
        """,
        [(cls.name, cls.description) for cls in CLASSES],
    )

    conn.executemany(
        """
        INSERT OR REPLACE INTO ontology_properties(name, domain_name, range_type, description)
        VALUES(?, ?, ?, ?)
        """,
        [
            (prop.name, prop.domain, prop.range_type, prop.description)
            for prop in PROPERTIES
        ],
    )

    conn.execute("DELETE FROM triples")
    conn.executemany(
        """
        INSERT INTO triples(subject, predicate, object_value)
        VALUES(?, ?, ?)
        """,
        [(t.subject, t.predicate, t.object_value) for t in TRIPLES],
    )
    conn.commit()


def get_assets_by_team(conn: sqlite3.Connection, team_id: str) -> List[Tuple[str, str]]:
    return conn.execute(
        """
        SELECT t.subject, typ.object_value AS asset_type
        FROM triples t
        JOIN triples typ
          ON typ.subject = t.subject
         AND typ.predicate = 'rdf:type'
        WHERE t.predicate = 'belongs_to_team'
          AND t.object_value = ?
        ORDER BY t.subject
        """,
        (team_id,),
    ).fetchall()


def get_upstream_dependencies(conn: sqlite3.Connection, asset_id: str) -> List[str]:
    rows = conn.execute(
        """
        SELECT object_value
        FROM triples
        WHERE subject = ?
          AND predicate = 'depends_on'
        ORDER BY object_value
        """,
        (asset_id,),
    ).fetchall()
    return [row[0] for row in rows]
