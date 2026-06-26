from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from ontology_storage import Ontology, OntologyError, OntologyStore


def build_ontology() -> Ontology:
    ontology = Ontology()
    ontology.add_class("ex:Person", "Person")
    ontology.add_class("ex:Patient", "Patient", parent="ex:Person")
    ontology.add_class("ex:Clinician", "Clinician", parent="ex:Person")
    ontology.add_class("ex:Department", "Department")

    ontology.add_property(
        "ex:hasName",
        "has name",
        domain="ex:Person",
        range="xsd:string",
        range_kind="literal",
    )
    ontology.add_property(
        "ex:treatedBy",
        "treated by",
        domain="ex:Patient",
        range="ex:Clinician",
    )
    ontology.add_property(
        "ex:belongsTo",
        "belongs to",
        domain="ex:Clinician",
        range="ex:Department",
    )
    return ontology


class OntologyStoreTest(unittest.TestCase):
    def test_subclass_can_use_parent_domain_property(self) -> None:
        with OntologyStore(build_ontology()) as store:
            store.add_instance("patient:001", "ex:Patient")

            store.add_literal("patient:001", "ex:hasName", "Alice")

            facts = store.describe("patient:001")
            self.assertIn("ex:Patient", store.direct_types("patient:001"))
            self.assertIn("ex:Person", store.inferred_types("patient:001"))
            self.assertTrue(
                any(
                    fact.predicate == "ex:hasName" and fact.object == "Alice"
                    for fact in facts
                )
            )

    def test_relation_requires_object_range_type(self) -> None:
        with OntologyStore(build_ontology()) as store:
            store.add_instance("patient:001", "ex:Patient")

            with self.assertRaisesRegex(OntologyError, "doctor:009 must be typed"):
                store.add_relation("patient:001", "ex:treatedBy", "doctor:009")

    def test_relation_rejects_wrong_subject_domain(self) -> None:
        with OntologyStore(build_ontology()) as store:
            store.add_instance("patient:001", "ex:Patient")
            store.add_instance("dept:cardiology", "ex:Department")

            with self.assertRaisesRegex(OntologyError, "patient:001 must be typed"):
                store.add_relation("patient:001", "ex:belongsTo", "dept:cardiology")

    def test_sqlite_database_persists_facts(self) -> None:
        ontology = build_ontology()
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "facts.sqlite"

            with OntologyStore(ontology, db_path) as store:
                store.add_instance("doctor:009", "ex:Clinician")
                store.add_literal("doctor:009", "ex:hasName", "Dr. Zhang")

            with OntologyStore(ontology, db_path) as store:
                facts = store.describe("doctor:009")

            self.assertEqual(len(facts), 2)
            self.assertEqual(
                sorted((fact.predicate, fact.object) for fact in facts),
                [("ex:hasName", "Dr. Zhang"), ("rdf:type", "ex:Clinician")],
            )


if __name__ == "__main__":
    unittest.main()
