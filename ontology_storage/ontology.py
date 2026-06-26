from dataclasses import dataclass
from typing import List


@dataclass(frozen=True)
class OntologyClass:
    name: str
    description: str


@dataclass(frozen=True)
class OntologyProperty:
    name: str
    domain: str
    range_type: str
    description: str


@dataclass(frozen=True)
class Triple:
    subject: str
    predicate: str
    object_value: str


CLASSES: List[OntologyClass] = [
    OntologyClass(name="Asset", description="企业资产的抽象父类"),
    OntologyClass(name="Server", description="计算服务器"),
    OntologyClass(name="Database", description="数据库实例"),
    OntologyClass(name="Team", description="负责资产的团队"),
]

PROPERTIES: List[OntologyProperty] = [
    OntologyProperty(
        name="belongs_to_team",
        domain="Asset",
        range_type="Team",
        description="资产归属团队",
    ),
    OntologyProperty(
        name="depends_on",
        domain="Asset",
        range_type="Asset",
        description="资产依赖关系",
    ),
    OntologyProperty(
        name="runs_on",
        domain="Database",
        range_type="Server",
        description="数据库运行所在服务器",
    ),
]

TRIPLES: List[Triple] = [
    Triple(subject="server-prod-1", predicate="rdf:type", object_value="Server"),
    Triple(subject="server-prod-2", predicate="rdf:type", object_value="Server"),
    Triple(subject="db-order", predicate="rdf:type", object_value="Database"),
    Triple(subject="db-user", predicate="rdf:type", object_value="Database"),
    Triple(subject="team-core-ai", predicate="rdf:type", object_value="Team"),
    Triple(subject="team-data-platform", predicate="rdf:type", object_value="Team"),
    Triple(subject="db-order", predicate="runs_on", object_value="server-prod-1"),
    Triple(subject="db-user", predicate="runs_on", object_value="server-prod-2"),
    Triple(subject="db-order", predicate="belongs_to_team", object_value="team-core-ai"),
    Triple(subject="db-user", predicate="belongs_to_team", object_value="team-data-platform"),
    Triple(subject="db-user", predicate="depends_on", object_value="db-order"),
]
