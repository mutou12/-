# ontology-storage-demo

一个极简可运行项目：演示**本体论（Ontology）如何和数据存储结合**。

核心目标：
- 用本体定义“类（Class）”和“属性（Property）”；
- 用三元组（subject-predicate-object）存业务事实；
- 用 SQL 把“语义层”查询成可用结果。

## 目录

```text
.
├── api
│   ├── __init__.py
│   ├── crud.py          # CRUD 逻辑
│   ├── database.py      # DB 连接与会话
│   ├── main.py          # FastAPI 入口
│   ├── models.py        # SQLAlchemy 模型
│   └── schemas.py       # Pydantic 请求/响应模型
├── demo.py
├── ontology_storage
│   ├── __init__.py
│   ├── ontology.py      # 本体定义 + 示例三元组
│   └── storage.py       # SQLite 建表、入库、查询
├── requirements.txt
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

## FastAPI 文档存储服务（content JSON 方案）

### 安装依赖

```bash
python3 -m pip install -r requirements.txt
```

### 启动服务

```bash
uvicorn api.main:app --reload
```

启动后访问：
- Swagger: `http://127.0.0.1:8000/docs`

### 示例：创建一条文档

```bash
curl -X POST "http://127.0.0.1:8000/docs" \
  -H "Content-Type: application/json" \
  -d '{
    "company_id": 1001,
    "doc_type": "financial_report",
    "doc_no": "FIN-2025-Q1",
    "status": "valid",
    "issue_date": "2025-04-20",
    "expiry_date": null,
    "content": {
      "report_period": "2025Q1",
      "revenue": 12000000,
      "net_profit": 2200000
    }
  }'
```

### 示例：按公司查询文档

```bash
curl "http://127.0.0.1:8000/companies/1001/docs?doc_type=financial_report"
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
