# Ontology Storage Demo

一个很小的 Python 原型，用来探索 **本体论（Ontology）在数据存储层的用法**。

核心想法：

- 用 ontology 定义领域概念：`Patient`、`Clinician`、`Department` 等。
- 用 RDF-style triple 存储事实：`subject predicate object`。
- 写入 SQLite 前做 ontology 校验：检查属性的 domain/range、类继承、IRI/字面量类型。
- 保持存储结构灵活，同时避免“随便塞脏关系”。

## 快速运行

```bash
PYTHONPATH=src python3 examples/healthcare_demo.py
python3 -m unittest
```

示例输出会展示：

- 患者相关 facts
- `Patient -> Person` 的继承推理
- 一条不符合 ontology 约束的写入被拒绝

## 项目结构

```text
src/ontology_storage/
  model.py      # ontology class/property 定义和继承判断
  store.py      # SQLite triple store + 写入校验
examples/
  healthcare_demo.py
tests/
  test_ontology_store.py
```

## 这个原型验证了什么

### 1. Ontology 可以作为存储层 schema

传统关系型 schema 更偏“表结构约束”，ontology 更偏“语义约束”：

```text
Patient is a Person
treatedBy: Patient -> Clinician
hasName: Person -> xsd:string
```

所以 `Patient` 可以写 `hasName`，因为 `Patient` 继承自 `Person`。

### 2. Triple store 适合表达稀疏、异构、关系密集的数据

事实统一存成：

```text
patient:001 rdf:type ex:Patient
patient:001 ex:hasName Alice
patient:001 ex:treatedBy doctor:009
```

新增概念或关系时，不需要改数据库表结构，只需要扩展 ontology。

### 3. 写入时校验比事后清洗更稳

比如 `ex:belongsTo` 的 domain 是 `ex:Clinician`，下面这条会被拒绝：

```python
store.add_relation("patient:001", "ex:belongsTo", "dept:cardiology")
```

这样能在入库边界保证数据语义正确。

## 后续可扩展方向

- 把 ontology 从 Python 代码换成 OWL/RDF 文件加载。
- 增加 SPARQL-like 查询层。
- 增加 materialized inference，把父类推理结果持久化。
- 接入向量库：ontology 管结构化语义，embedding 管模糊召回。
- 接入业务服务 API：在请求写入前统一走 ontology validation。
