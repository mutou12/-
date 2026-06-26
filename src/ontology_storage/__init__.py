"""Ontology-aware data storage demo."""

from .model import Ontology, OntologyClass, OntologyError, OntologyProperty
from .store import RDF_TYPE, Fact, OntologyStore

__all__ = [
    "Fact",
    "Ontology",
    "OntologyClass",
    "OntologyError",
    "OntologyProperty",
    "OntologyStore",
    "RDF_TYPE",
]
