"""Run a small ontology-backed storage demo.

Execute from repo root:

    PYTHONPATH=src python3 examples/healthcare_demo.py
"""

from ontology_storage import Ontology, OntologyError, OntologyStore


def build_healthcare_ontology() -> Ontology:
    ontology = Ontology()
    ontology.add_class("ex:Person", "Person")
    ontology.add_class("ex:Patient", "Patient", parent="ex:Person")
    ontology.add_class("ex:Clinician", "Clinician", parent="ex:Person")
    ontology.add_class("ex:Department", "Department")
    ontology.add_class("ex:Condition", "Condition")

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
    ontology.add_property(
        "ex:diagnosedWith",
        "diagnosed with",
        domain="ex:Patient",
        range="ex:Condition",
    )
    return ontology


def main() -> None:
    ontology = build_healthcare_ontology()

    with OntologyStore(ontology) as store:
        store.add_instance("patient:001", "ex:Patient")
        store.add_instance("doctor:009", "ex:Clinician")
        store.add_instance("dept:cardiology", "ex:Department")
        store.add_instance("condition:hypertension", "ex:Condition")

        store.add_literal("patient:001", "ex:hasName", "Alice")
        store.add_literal("doctor:009", "ex:hasName", "Dr. Zhang")
        store.add_relation("patient:001", "ex:treatedBy", "doctor:009")
        store.add_relation("doctor:009", "ex:belongsTo", "dept:cardiology")
        store.add_relation("patient:001", "ex:diagnosedWith", "condition:hypertension")

        print("Facts about patient:001")
        for fact in store.describe("patient:001"):
            print(f"- {fact.subject} {fact.predicate} {fact.object} ({fact.object_kind})")

        print("\nInferred patient types:")
        for class_iri in sorted(store.inferred_types("patient:001")):
            print(f"- {class_iri}")

        print("\nRejected invalid write:")
        try:
            store.add_relation("patient:001", "ex:belongsTo", "dept:cardiology")
        except OntologyError as exc:
            print(f"- {exc}")


if __name__ == "__main__":
    main()
