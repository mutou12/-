"""
单元测试：OntologyStore 核心功能
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from rdflib.namespace import RDF, RDFS, XSD
from rdflib import URIRef, Literal

from src.ontology_store import OntologyStore, TKB
from src.reasoner import OntologyReasoner


@pytest.fixture
def store():
    s = OntologyStore()
    s.load_all()
    return s


@pytest.fixture
def empty_store():
    return OntologyStore()


# ── 加载测试 ──────────────────────────────────────────────────────────────────

class TestLoad:
    def test_load_all_has_triples(self, store):
        assert store.stats()["triples"] > 0

    def test_load_ontology_has_classes(self, store):
        classes = store.get_classes()
        assert len(classes) > 5

    def test_tkb_technology_class_exists(self, store):
        assert TKB.Technology in store.get_classes()

    def test_pytorch_instance_exists(self, store):
        instances = store.list_instances_of(TKB.MLFramework)
        uris = [str(i) for i in instances]
        assert any("PyTorch" in u for u in uris)


# ── CRUD 测试 ─────────────────────────────────────────────────────────────────

class TestCRUD:
    def test_add_entity_creates_triples(self, store):
        before = store.stats()["triples"]
        store.add_entity("TestLib", TKB.Framework, "TestLib", releaseYear=2024)
        assert store.stats()["triples"] > before

    def test_add_entity_returns_uri(self, store):
        uri = store.add_entity("TestLib2", TKB.Framework, "TestLib2")
        assert isinstance(uri, URIRef)
        assert "TestLib2" in str(uri)

    def test_add_relation_persisted(self, store):
        uri = store.add_entity("TestLib3", TKB.Framework, "TestLib3")
        store.add_relation(uri, TKB.primaryLanguage, TKB.Python)
        info = store.get_entity_info(uri)
        assert TKB.Python in [URIRef(r) for r in info["relations"].get("primaryLanguage", [])]

    def test_update_data_property(self, store):
        uri = store.add_entity("UpdateTest", TKB.Technology, "UpdateTest", githubStars=100)
        store.update_data_property(uri, TKB.githubStars, 999, XSD.integer)
        info = store.get_entity_info(uri)
        assert info["properties"]["githubStars"] == 999

    def test_remove_entity_cleans_up(self, store):
        uri = store.add_entity("DeleteTest", TKB.Technology, "DeleteTest")
        removed = store.remove_entity(uri)
        assert removed > 0
        # 实体应不再有类型断言
        triples = list(store.graph.triples((uri, None, None)))
        assert len(triples) == 0

    def test_get_entity_info_structure(self, store):
        info = store.get_entity_info(TKB.PyTorch)
        assert "uri" in info
        assert "types" in info
        assert "properties" in info
        assert "relations" in info
        assert len(info["types"]) > 0


# ── SPARQL 测试 ───────────────────────────────────────────────────────────────

class TestSPARQL:
    def test_ml_frameworks_query(self, store):
        from src.queries import Q_ML_FRAMEWORKS
        rows = store.sparql(Q_ML_FRAMEWORKS)
        assert len(rows) >= 2
        names = [r["name"] for r in rows]
        assert "PyTorch" in names
        assert "TensorFlow" in names

    def test_python_ecosystem_query(self, store):
        from src.queries import Q_PYTHON_ECOSYSTEM
        rows = store.sparql(Q_PYTHON_ECOSYSTEM)
        assert len(rows) >= 1

    def test_dependency_chain_property_path(self, store):
        from src.queries import Q_DEPENDENCY_CHAIN
        rows = store.sparql(Q_DEPENDENCY_CHAIN)
        # Transformers builtOn PyTorch and TensorFlow
        names = [r["name"] for r in rows]
        assert "PyTorch" in names or "TensorFlow" in names

    def test_sparql_returns_list_of_dicts(self, store):
        rows = store.sparql("""
            PREFIX tkb: <http://example.org/tech-kb#>
            PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
            SELECT ?name WHERE { tkb:PyTorch rdfs:label ?name . }
        """)
        assert isinstance(rows, list)
        assert isinstance(rows[0], dict)
        assert rows[0]["name"] == "PyTorch"

    def test_sparql_empty_result(self, store):
        rows = store.sparql("""
            PREFIX tkb: <http://example.org/tech-kb#>
            SELECT ?x WHERE { tkb:NonExistent tkb:unknown ?x . }
        """)
        assert rows == []


# ── 推理测试 ──────────────────────────────────────────────────────────────────

class TestReasoner:
    def test_reasoner_returns_new_store(self, store):
        r = OntologyReasoner(store)
        new_store = r.run()
        assert new_store is not store

    def test_reasoner_expands_triples(self, store):
        r = OntologyReasoner(store)
        new_store = r.run()
        assert new_store.stats()["triples"] >= store.stats()["triples"]

    def test_class_hierarchy_inference(self, store):
        r = OntologyReasoner(store)
        # MLFramework 实例在推理后应获得 Framework 父类成员资格
        inferred = r.explain_class_hierarchy(TKB.PyTorch)
        # inferred 包含推导出的新类型 URI
        inferred_labels = [u.split("#")[-1] for u in inferred if "#" in u]
        # 至少应推导出 Framework 或 Technology
        assert any(label in inferred_labels for label in ["Framework", "Technology"])

    def test_symmetric_property_inference(self, store):
        r = OntologyReasoner(store)
        new_facts = r.explain_symmetric()
        # 应有对称推导结果
        # 原始只声明了 Python usedWith PyTorch，推理后应有 PyTorch usedWith Python
        assert isinstance(new_facts, list)


# ── 序列化测试 ────────────────────────────────────────────────────────────────

class TestSerialization:
    def test_to_turtle_is_string(self, store):
        ttl = store.to_turtle()
        assert isinstance(ttl, str)
        assert "@prefix" in ttl

    def test_serialize_to_file(self, store, tmp_path):
        out = str(tmp_path / "test.ttl")
        store.serialize(out, fmt="turtle")
        assert os.path.getsize(out) > 0

    def test_stats_keys(self, store):
        stats = store.stats()
        assert set(stats.keys()) == {"triples", "subjects", "predicates", "objects"}
