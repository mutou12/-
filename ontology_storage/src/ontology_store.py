"""
OntologyStore：基于 RDFLib 的三元组存储核心层

知识表示方式：
  每条知识 = (Subject, Predicate, Object) 三元组
  对比关系型 DB 的 (table, column, value)，本体论用语义关系网络代替平铺表格
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Optional, Iterator

from rdflib import Graph, Namespace, URIRef, Literal, BNode
from rdflib.namespace import OWL, RDF, RDFS, XSD


TKB = Namespace("http://example.org/tech-kb#")

ONTOLOGY_DIR = Path(__file__).parent.parent / "ontology"


class OntologyStore:
    """
    封装 rdflib.Graph，提供：
    - 加载本体 + 实例数据
    - CRUD 操作（添加/查询/删除三元组）
    - 序列化持久化
    - SPARQL 查询接口
    """

    def __init__(self, store_path: Optional[str] = None):
        """
        store_path: 若提供，使用 SQLite 持久化后端（rdflib-sqlalchemy）
                    否则使用内存图（适合演示和测试）
        """
        self.graph = Graph()
        self.graph.bind("tkb", TKB)
        self.graph.bind("owl", OWL)
        self._store_path = store_path

    # ── 加载 ─────────────────────────────────────────────────────────────────

    def load_ontology(self, path: Optional[str] = None) -> "OntologyStore":
        """加载本体定义（TBox）"""
        p = Path(path) if path else ONTOLOGY_DIR / "tech_kb.ttl"
        self.graph.parse(str(p), format="turtle")
        return self

    def load_instances(self, path: Optional[str] = None) -> "OntologyStore":
        """加载实例数据（ABox）"""
        p = Path(path) if path else ONTOLOGY_DIR / "instances.ttl"
        self.graph.parse(str(p), format="turtle")
        return self

    def load_all(self) -> "OntologyStore":
        return self.load_ontology().load_instances()

    # ── 写操作（CRUD） ────────────────────────────────────────────────────────

    def add_entity(
        self,
        name: str,
        class_uri: URIRef,
        label: str,
        **data_props,
    ) -> URIRef:
        """
        添加一个实体（个体）及其数据属性。

        name       : 本地名称，如 "LangChain"
        class_uri  : 所属类，如 TKB.Framework
        label      : rdfs:label
        data_props : 键值对，键为属性本地名，值为字面量
        """
        uri = TKB[name]
        self.graph.add((uri, RDF.type, class_uri))
        self.graph.add((uri, RDFS.label, Literal(label)))
        for prop_name, value in data_props.items():
            prop = TKB[prop_name]
            if isinstance(value, int):
                self.graph.add((uri, prop, Literal(value, datatype=XSD.integer)))
            else:
                self.graph.add((uri, prop, Literal(str(value))))
        return uri

    def add_relation(self, subject: URIRef, predicate: URIRef, obj: URIRef) -> None:
        """添加对象属性三元组"""
        self.graph.add((subject, predicate, obj))

    def remove_entity(self, uri: URIRef) -> int:
        """删除实体相关的所有三元组（作为主语或宾语），返回删除数量"""
        triples_s = list(self.graph.triples((uri, None, None)))
        triples_o = list(self.graph.triples((None, None, uri)))
        for t in triples_s + triples_o:
            self.graph.remove(t)
        return len(triples_s) + len(triples_o)

    def update_data_property(
        self, uri: URIRef, prop: URIRef, new_value, datatype=None
    ) -> None:
        """更新某实体的一个数据属性（先删后增）"""
        self.graph.remove((uri, prop, None))
        if datatype:
            self.graph.add((uri, prop, Literal(new_value, datatype=datatype)))
        elif isinstance(new_value, int):
            self.graph.add((uri, prop, Literal(new_value, datatype=XSD.integer)))
        else:
            self.graph.add((uri, prop, Literal(str(new_value))))

    # ── 基础查询 ──────────────────────────────────────────────────────────────

    def get_entity_info(self, uri: URIRef) -> dict:
        """返回某实体所有属性的字典"""
        result = {"uri": str(uri), "types": [], "properties": {}, "relations": {}}
        for _, p, o in self.graph.triples((uri, None, None)):
            if p == RDF.type:
                result["types"].append(str(o))
            elif isinstance(o, Literal):
                key = p.split("#")[-1] if "#" in str(p) else str(p)
                result["properties"][key] = o.toPython()
            elif isinstance(o, URIRef):
                key = p.split("#")[-1] if "#" in str(p) else str(p)
                result["relations"].setdefault(key, []).append(str(o))
        return result

    def list_instances_of(self, class_uri: URIRef) -> list[URIRef]:
        """列出某类的所有直接实例"""
        return [s for s, _, _ in self.graph.triples((None, RDF.type, class_uri))]

    def get_classes(self) -> list[URIRef]:
        """返回本体中定义的所有类"""
        return [
            s
            for s, _, _ in self.graph.triples((None, RDF.type, OWL.Class))
            if isinstance(s, URIRef)
        ]

    def sparql(self, query: str) -> list[dict]:
        """
        执行 SPARQL SELECT 查询，返回行列表（每行是变量名→值的字典）。
        """
        qres = self.graph.query(query)
        rows = []
        for row in qres:
            record = {}
            for i, var in enumerate(qres.vars):
                # 用索引取值，避免与 ResultRow 内置方法（如 .count）命名冲突
                val = row[i]
                if val is not None:
                    record[str(var)] = val.toPython() if isinstance(val, Literal) else str(val)
                else:
                    record[str(var)] = None
            rows.append(record)
        return rows

    # ── 序列化 ────────────────────────────────────────────────────────────────

    def serialize(self, path: str, fmt: str = "turtle") -> None:
        """将当前图序列化到文件"""
        self.graph.serialize(destination=path, format=fmt)

    def to_turtle(self) -> str:
        """返回 Turtle 格式字符串"""
        return self.graph.serialize(format="turtle")

    def stats(self) -> dict:
        """图统计信息"""
        return {
            "triples": len(self.graph),
            "subjects": len(set(self.graph.subjects())),
            "predicates": len(set(self.graph.predicates())),
            "objects": len(set(self.graph.objects())),
        }
