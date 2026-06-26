"""Ontology definitions used by the storage layer."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

ValueKind = Literal["iri", "literal"]


class OntologyError(ValueError):
    """Raised when ontology definitions or data violate ontology rules."""


@dataclass(frozen=True)
class OntologyClass:
    """A domain concept in the ontology."""

    iri: str
    label: str
    parent: str | None = None


@dataclass(frozen=True)
class OntologyProperty:
    """A typed edge between two ontology concepts, or a concept and a literal."""

    iri: str
    label: str
    domain: str
    range: str
    range_kind: ValueKind = "iri"


@dataclass
class Ontology:
    """In-memory ontology catalog.

    The storage layer uses this catalog to validate class membership and property
    writes before persisting facts.
    """

    classes: dict[str, OntologyClass] = field(default_factory=dict)
    properties: dict[str, OntologyProperty] = field(default_factory=dict)

    def add_class(self, iri: str, label: str, parent: str | None = None) -> None:
        if iri in self.classes:
            raise OntologyError(f"class already exists: {iri}")
        if parent is not None and parent not in self.classes:
            raise OntologyError(f"parent class does not exist: {parent}")
        self.classes[iri] = OntologyClass(iri=iri, label=label, parent=parent)

    def add_property(
        self,
        iri: str,
        label: str,
        domain: str,
        range: str,
        range_kind: ValueKind = "iri",
    ) -> None:
        if iri in self.properties:
            raise OntologyError(f"property already exists: {iri}")
        if domain not in self.classes:
            raise OntologyError(f"property domain does not exist: {domain}")
        if range_kind == "iri" and range not in self.classes:
            raise OntologyError(f"property range class does not exist: {range}")
        if range_kind not in ("iri", "literal"):
            raise OntologyError(f"unsupported range kind: {range_kind}")
        self.properties[iri] = OntologyProperty(
            iri=iri,
            label=label,
            domain=domain,
            range=range,
            range_kind=range_kind,
        )

    def require_class(self, iri: str) -> OntologyClass:
        try:
            return self.classes[iri]
        except KeyError as exc:
            raise OntologyError(f"unknown class: {iri}") from exc

    def require_property(self, iri: str) -> OntologyProperty:
        try:
            return self.properties[iri]
        except KeyError as exc:
            raise OntologyError(f"unknown property: {iri}") from exc

    def is_subclass_of(self, child: str, ancestor: str) -> bool:
        """Return whether ``child`` is ``ancestor`` or inherits from it."""

        self.require_class(child)
        self.require_class(ancestor)

        current: str | None = child
        while current is not None:
            if current == ancestor:
                return True
            current = self.classes[current].parent
        return False

    def matching_classes(self, concrete_types: set[str], required_type: str) -> set[str]:
        """Return concrete types that satisfy a required ontology class."""

        self.require_class(required_type)
        return {
            type_iri
            for type_iri in concrete_types
            if self.is_subclass_of(type_iri, required_type)
        }
