# Ontology Storage Explorer

探索**本体论（Ontology）在数据存储中的应用**，以"技术知识库"为领域，对比
RDF/OWL 三元组存储与传统关系型存储（SQLite）在数据建模、查询表达力、语义推断
三个维度的核心差异。

## 核心概念地图

```
传统存储                       本体论存储
─────────                     ─────────────────────────
Table        ←→               Class (owl:Class)
Row          ←→               Individual (实例)
Column       ←→               DataProperty (数据属性)
Foreign Key  ←→               ObjectProperty (对象属性/关系)
JOIN         ←→               SPARQL Property Path
Trigger      ←→               OWL 推理规则（自动推导）
Schema DDL   ←→               无 Schema（任意扩展三元组）
```

## 项目结构

```
ontology_storage/
├── ontology/
│   ├── tech_kb.ttl      # 本体定义 TBox：类、属性、公理
│   └── instances.ttl    # 实例数据 ABox：具体技术栈数据
├── src/
│   ├── ontology_store.py  # 核心存储层（CRUD + SPARQL）
│   ├── reasoner.py        # OWL-RL 推理层
│   ├── queries.py         # 预定义 SPARQL 查询集
│   └── sql_comparison.py  # 关系型存储对照实现
├── examples/
│   ├── 01_basic_crud.py       # 三元组增删改查
│   ├── 02_sparql_queries.py   # 9 个 SPARQL 查询示例
│   ├── 03_reasoning.py        # OWL 推理：对称/传递/子类
│   └── 04_comparison.py       # RDF vs SQL 横向对比
├── tests/
│   └── test_ontology_store.py # 22 个单元测试
├── run_all.py           # 一键运行所有示例
└── requirements.txt
```

## 安装

```bash
pip install -r requirements.txt
```

## 运行

```bash
# 一键跑全部示例
python3 run_all.py

# 或单独运行
python3 examples/01_basic_crud.py
python3 examples/02_sparql_queries.py
python3 examples/03_reasoning.py
python3 examples/04_comparison.py

# 测试
python3 -m pytest tests/ -v
```

## 领域模型（本体）

**类层次（TBox）**

```
Technology
├── ProgrammingLanguage
├── Framework
│   ├── MLFramework        # PyTorch, TensorFlow, Transformers
│   └── WebFramework       # FastAPI, Django
└── Database
    ├── GraphDatabase      # Neo4j
    ├── RelationalDatabase # PostgreSQL
    └── VectorDatabase     # Milvus, ChromaDB
```

**核心关系（ObjectProperty）**

| 属性 | OWL 特性 | 语义 |
|------|----------|------|
| `usedWith` | SymmetricProperty | 常配合使用，声明一方推理自动双向 |
| `builtOn` | TransitiveProperty | 依赖关系，自动推导传递闭包 |
| `competitorOf` | SymmetricProperty | 竞争关系 |
| `primaryLanguage` | - | 框架主语言 |
| `createdBy` | - | 创建组织 |

## 关键演示要点

### 1. Schema-free 扩展
RDF 无需 DDL，任意时刻添加新关系类型：
```python
store.add_relation(TKB.Milvus, TKB["recommendedFor"], TKB["AIApplication"])
```

### 2. SPARQL 路径查询
单条语句表达多跳图遍历（等价于多层 JOIN）：
```sparql
SELECT ?name WHERE {
    tkb:Transformers tkb:builtOn+ ?dep .   # + 表示一跳或多跳传递
    ?dep rdfs:label ?name .
}
```

### 3. OWL 推理自动推导隐含知识
```
已知: PyTorch rdf:type MLFramework
已知: MLFramework rdfs:subClassOf Framework
推理: PyTorch rdf:type Framework  ← 自动推导，无需手动维护

已知: Python tkb:usedWith PyTorch   (usedWith 是 owl:SymmetricProperty)
推理: PyTorch tkb:usedWith Python   ← 推理引擎自动补全
```

## 适用场景

| 场景 | 推荐方案 |
|------|----------|
| 结构固定、高并发 OLTP | 关系型数据库（PostgreSQL / MySQL）|
| 动态知识图谱、语义搜索 | RDF 三元组存储（本项目方案）|
| 多源异构数据集成 | 本体论统一建模 + SPARQL 联合查询 |
| 需要逻辑推断的 AI 知识库 | OWL + 推理引擎 |

## 技术栈

- **rdflib** — Python RDF 图操作核心库
- **owlrl** — OWL-RL 推理规则引擎
- **rich** — 终端美化输出
- **pytest** — 单元测试
