"""SQLite-backed ontology-aware triple store."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from .model import Ontology, OntologyError

RDF_TYPE = "rdf:type"


@dataclass(frozen=True)
class Fact:
    subject: str
    predicate: str
    object: str
    object_kind: str


class OntologyStore:
    """Persist ontology facts as RDF-style triples in SQLite.

    The store is intentionally small: it demonstrates the core pattern of using
    ontology metadata as a write-time contract for otherwise flexible graph data.
    """

    def __init__(self, ontology: Ontology, db_path: str | Path = ":memory:") -> None:
        self.ontology = ontology
        self.connection = sqlite3.connect(str(db_path))
        self.connection.row_factory = sqlite3.Row
        self._ensure_schema()

    def close(self) -> None:
        self.connection.close()

    def __enter__(self) -> "OntologyStore":
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    def _ensure_schema(self) -> None:
        self.connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS facts (
                subject TEXT NOT NULL,
                predicate TEXT NOT NULL,
                object TEXT NOT NULL,
                object_kind TEXT NOT NULL CHECK (object_kind IN ('iri', 'literal')),
                PRIMARY KEY (subject, predicate, object, object_kind)
            );

            CREATE INDEX IF NOT EXISTS idx_facts_subject ON facts(subject);
            CREATE INDEX IF NOT EXISTS idx_facts_predicate ON facts(predicate);
            CREATE INDEX IF NOT EXISTS idx_facts_object ON facts(object);
            """
        )

    def add_instance(self, subject: str, class_iri: str) -> None:
        """Declare that a resource is an instance of an ontology class."""

        self.ontology.require_class(class_iri)
        self._insert(Fact(subject, RDF_TYPE, class_iri, "iri"))

    def add_relation(self, subject: str, predicate: str, object_iri: str) -> None:
        """Add a typed resource-to-resource edge."""

        self._validate_property_fact(subject, predicate, object_iri, "iri")
        self._insert(Fact(subject, predicate, object_iri, "iri"))

    def add_literal(self, subject: str, predicate: str, value: str) -> None:
        """Add a typed resource-to-literal edge."""

        self._validate_property_fact(subject, predicate, value, "literal")
        self._insert(Fact(subject, predicate, value, "literal"))

    def _validate_property_fact(
        self,
        subject: str,
        predicate: str,
        object_value: str,
        object_kind: str,
    ) -> None:
        property_ = self.ontology.require_property(predicate)
        if property_.range_kind != object_kind:
            raise OntologyError(
                f"{predicate} expects {property_.range_kind}, got {object_kind}"
            )

        subject_types = self.direct_types(subject)
        if not self.ontology.matching_classes(subject_types, property_.domain):
            raise OntologyError(
                f"{subject} must be typed as {property_.domain} or a subclass before using {predicate}"
            )

        if object_kind == "iri":
            object_types = self.direct_types(object_value)
            if not self.ontology.matching_classes(object_types, property_.range):
                raise OntologyError(
                    f"{object_value} must be typed as {property_.range} or a subclass before using {predicate}"
                )

    def _insert(self, fact: Fact) -> None:
        with self.connection:
            self.connection.execute(
                """
                INSERT OR IGNORE INTO facts(subject, predicate, object, object_kind)
                VALUES (?, ?, ?, ?)
                """,
                (fact.subject, fact.predicate, fact.object, fact.object_kind),
            )

    def direct_types(self, subject: str) -> set[str]:
        rows = self.connection.execute(
            """
            SELECT object
            FROM facts
            WHERE subject = ? AND predicate = ? AND object_kind = 'iri'
            """,
            (subject, RDF_TYPE),
        ).fetchall()
        return {row["object"] for row in rows}

    def inferred_types(self, subject: str) -> set[str]:
        """Return direct classes plus all parent classes implied by the ontology."""

        inferred: set[str] = set()
        pending = list(self.direct_types(subject))
        while pending:
            class_iri = pending.pop()
            if class_iri in inferred:
                continue
            inferred.add(class_iri)
            parent = self.ontology.require_class(class_iri).parent
            if parent is not None:
                pending.append(parent)
        return inferred

    def facts(
        self,
        *,
        subject: str | None = None,
        predicate: str | None = None,
        object: str | None = None,
    ) -> list[Fact]:
        """Query facts by optional subject, predicate and object filters."""

        filters: list[str] = []
        params: list[str] = []
        if subject is not None:
            filters.append("subject = ?")
            params.append(subject)
        if predicate is not None:
            filters.append("predicate = ?")
            params.append(predicate)
        if object is not None:
            filters.append("object = ?")
            params.append(object)

        where = f"WHERE {' AND '.join(filters)}" if filters else ""
        rows = self.connection.execute(
            f"""
            SELECT subject, predicate, object, object_kind
            FROM facts
            {where}
            ORDER BY subject, predicate, object
            """,
            params,
        ).fetchall()
        return [Fact(**dict(row)) for row in rows]

    def describe(self, subject: str) -> list[Fact]:
        """Return all known facts about one resource."""

        return self.facts(subject=subject)

    def bulk_load(self, facts: Iterable[Fact]) -> None:
        """Load pre-validated facts.

        This is useful for fixtures or migrations. Application writes should use
        ``add_instance``, ``add_relation`` and ``add_literal`` to keep validation on.
        """

        for fact in facts:
            if fact.predicate == RDF_TYPE:
                self.add_instance(fact.subject, fact.object)
            elif fact.object_kind == "iri":
                self.add_relation(fact.subject, fact.predicate, fact.object)
            else:
                self.add_literal(fact.subject, fact.predicate, fact.object)
