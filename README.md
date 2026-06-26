# ontology-storage-demo

一个极简可运行项目：演示**本体论（Ontology）如何和数据存储结合**。

核心目标：
- 用本体定义“类（Class）”和“属性（Property）”；
- 用三元组（subject-predicate-object）存业务事实；
- 用 SQL 把“语义层”查询成可用结果。

## 目录

```text
.
├── demo.py
├── ontology_storage
│   ├── __init__.py
│   ├── ontology.py      # 本体定义 + 示例三元组
│   └── storage.py       # SQLite 建表、入库、查询
└── README.md
```

## 快速运行

```bash
python3 demo.py
```

预期输出（示例）：

```text
=== team-core-ai 负责的资产 ===
- db-order (Database)

=== db-user 的上游依赖 ===
- db-order
```

## 这套结构解决了什么

传统关系型表擅长“字段存储”，但对“语义关系”表达弱。  
本体 + 三元组的模式可以把数据分成两层：

1. **本体层（Schema/Semantics）**
   - `ontology_classes`
   - `ontology_properties`
2. **事实层（Facts）**
   - `triples`

这样你可以在不改表结构的情况下，扩展新的关系（比如 `replicates_to`、`owns_cost_center`）。

## 下一步可扩展方向

- 增加推理层：基于规则做派生关系（如 transitive dependency）。
- 接入图数据库：把 triples 迁移到 Neo4j/RDF store。
- 暴露 API：用 FastAPI 做查询接口，供服务调用。
