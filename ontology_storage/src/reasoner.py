"""
OntologyReasoner：OWL-RL 推理层

在原始三元组之上，利用 OWL 语义推导出隐含知识：
  - 对称属性推理：A usedWith B  →  B usedWith A
  - 传递属性推理：A builtOn B, B builtOn C  →  A builtOn C
  - 类层次推理：x ∈ MLFramework  →  x ∈ Framework  →  x ∈ Technology
  - 逆属性等其他规则...
"""
from __future__ import annotations

import copy
from typing import Optional

from rdflib import Graph, URIRef, Literal
from rdflib.namespace import OWL, RDF, RDFS

try:
    import owlrl
    HAS_OWLRL = True
except ImportError:
    HAS_OWLRL = False

from .ontology_store import OntologyStore, TKB


class OntologyReasoner:
    """
    基于 owlrl 做 OWL-RL（Rule Language）闭包推理，
    返回一个包含推导三元组的新 OntologyStore。
    """

    def __init__(self, store: OntologyStore):
        self.store = store

    def run(self) -> "OntologyStore":
        """
        对当前图做完整 OWL-RL 推理，返回扩充后的新 OntologyStore。
        原始 store 不被修改。
        """
        if not HAS_OWLRL:
            raise RuntimeError("owlrl 未安装，请 pip install owlrl")

        # 复制图，避免污染原始数据
        inferred_graph = Graph()
        for triple in self.store.graph:
            inferred_graph.add(triple)

        # 绑定命名空间
        for prefix, ns in self.store.graph.namespaces():
            inferred_graph.bind(prefix, ns)

        # 触发 OWL-RL 推理闭包
        owlrl.DeductiveClosure(owlrl.OWLRL_Semantics).expand(inferred_graph)

        new_store = OntologyStore()
        new_store.graph = inferred_graph
        return new_store

    def explain_symmetric(self) -> list[tuple[str, str, str]]:
        """
        展示对称属性（usedWith、competitorOf）产生的隐含三元组。
        对比推理前后的差异。
        """
        before = set(self.store.graph.triples((None, TKB.usedWith, None)))
        before |= set(self.store.graph.triples((None, TKB.competitorOf, None)))

        reasoned = self.run()
        after = set(reasoned.graph.triples((None, TKB.usedWith, None)))
        after |= set(reasoned.graph.triples((None, TKB.competitorOf, None)))

        new_facts = after - before
        return [
            (
                self._local_name(s),
                self._local_name(p),
                self._local_name(o),
            )
            for s, p, o in sorted(new_facts, key=lambda t: str(t[0]))
            if isinstance(s, URIRef) and isinstance(o, URIRef)
        ]

    def explain_transitive(self) -> list[tuple[str, str, str]]:
        """展示 builtOn 传递属性产生的推导三元组"""
        before = set(self.store.graph.triples((None, TKB.builtOn, None)))
        reasoned = self.run()
        after = set(reasoned.graph.triples((None, TKB.builtOn, None)))
        new_facts = after - before
        return [
            (self._local_name(s), "builtOn", self._local_name(o))
            for s, p, o in sorted(new_facts, key=lambda t: str(t[0]))
            if isinstance(s, URIRef) and isinstance(o, URIRef)
        ]

    def explain_class_hierarchy(self, instance_uri: URIRef) -> list[str]:
        """
        给定一个实例，列出推理前后它所属的所有类（利用子类传递推理）。
        """
        before = {
            str(o)
            for _, _, o in self.store.graph.triples((instance_uri, RDF.type, None))
        }
        reasoned = self.run()
        after = {
            str(o)
            for _, _, o in reasoned.graph.triples((instance_uri, RDF.type, None))
            if isinstance(o, URIRef)
        }
        return sorted(after - before)

    @staticmethod
    def _local_name(uri) -> str:
        s = str(uri)
        return s.split("#")[-1] if "#" in s else s.split("/")[-1]
