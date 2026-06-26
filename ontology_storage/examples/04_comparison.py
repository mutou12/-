"""
示例 04：本体论存储 vs 关系型存储（SQLite）对比

从以下4个维度横向比较：
  1. Schema 灵活性 —— 添加新关系类型
  2. 查询表达力 —— 图路径遍历
  3. 语义推断    —— 隐式知识发现
  4. 互操作性   —— 标准化格式
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from rich.console import Console
from rich.table import Table
from rich import box

from src.ontology_store import OntologyStore, TKB
from src.sql_comparison import SQLStorage
from src.reasoner import OntologyReasoner

console = Console()


def section(title: str):
    console.rule(f"[bold yellow]{title}")


def main():
    console.rule("[bold blue]04 · 本体论存储 vs 关系型存储（SQLite）对比")

    sql = SQLStorage()
    rdf = OntologyStore().load_all()

    # ── 1. Schema 灵活性 ───────────────────────────────────────────────────
    section("① Schema 灵活性：添加新关系类型 recommendedFor")

    sql_result = sql.add_new_relation_type()
    console.print(f"  [red]SQL[/]  : {sql_result}  ← 需要 DDL，影响已有代码")
    console.print(f"  [green]RDF[/]  : 直接 graph.add((TKB.Milvus, TKB.recommendedFor, TKB.AIApp)) — 无需 schema 变更")
    rdf.add_relation(TKB.Milvus, TKB["recommendedFor"], TKB["AIApplication"])
    console.print(f"  [green]✓[/] RDF 图中已添加 recommendedFor 关系，当前三元组数: {rdf.stats()['triples']}")

    # ── 2. 查询表达力 ──────────────────────────────────────────────────────
    section("② 查询表达力：Python 生态（usedWith）")

    sql_rows = sql.query_python_ecosystem()
    rdf_rows = rdf.sparql("""
        PREFIX tkb: <http://example.org/tech-kb#>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        SELECT ?name WHERE {
            tkb:Python tkb:usedWith ?t . ?t rdfs:label ?name .
        }
    """)
    sql_names = sorted(r["name"] for r in sql_rows)
    rdf_names = sorted(r["name"] for r in rdf_rows)

    t = Table(box=box.SIMPLE, title="Python usedWith 结果对比")
    t.add_column("SQL 结果", style="red")
    t.add_column("RDF 结果（推理前）", style="green")
    max_len = max(len(sql_names), len(rdf_names))
    for i in range(max_len):
        t.add_row(
            sql_names[i] if i < len(sql_names) else "",
            rdf_names[i] if i < len(rdf_names) else "",
        )
    console.print(t)

    console.print(
        "[dim]注：SQL 中 usedWith 对称性靠手动双向插入维护；\n"
        "RDF 中 usedWith 声明为 owl:SymmetricProperty，推理后自动双向[/]"
    )

    # 推理后的 RDF 结果
    reasoned = OntologyReasoner(rdf).run()
    rdf_rows_after = reasoned.sparql("""
        PREFIX tkb: <http://example.org/tech-kb#>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        SELECT ?name WHERE {
            tkb:Python tkb:usedWith ?t . ?t rdfs:label ?name .
        } ORDER BY ?name
    """)
    console.print(f"  RDF 推理后 Python usedWith: {[r['name'] for r in rdf_rows_after]}")

    # ── 3. 语义推断 ────────────────────────────────────────────────────────
    section("③ 语义推断：MLFramework 实例是否同时是 Framework？")

    sql_check = sql.conn.execute(
        "SELECT name FROM technologies WHERE type='MLFramework'"
    ).fetchall()
    console.print(f"  SQL: MLFramework 只是字符串标记，[red]无法自动推导父类关系[/]")
    console.print(f"       查询 Framework 类实例时，必须手写 WHERE type IN ('MLFramework','WebFramework',...)")

    framework_query = """
        PREFIX tkb: <http://example.org/tech-kb#>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        SELECT ?name WHERE { ?x a tkb:Framework ; rdfs:label ?name . }
    """
    before_names = sorted(r["name"] for r in rdf.sparql(framework_query))
    after_names  = sorted(r["name"] for r in reasoned.sparql(framework_query))

    console.print(f"\n  RDF 推理前 tkb:Framework 成员: {before_names}")
    console.print(f"  RDF 推理后 tkb:Framework 成员: {after_names}")
    console.print(f"  [green]新增（从 MLFramework/WebFramework 子类推导）: {sorted(set(after_names) - set(before_names))}[/]")

    # ── 4. 互操作性 ────────────────────────────────────────────────────────
    section("④ 互操作性：导出格式对比")

    import tempfile, os
    with tempfile.TemporaryDirectory() as tmp:
        ttl_path = os.path.join(tmp, "export.ttl")
        json_path = os.path.join(tmp, "export.jsonld")
        rdf.serialize(ttl_path, fmt="turtle")
        rdf.serialize(json_path, fmt="json-ld")
        ttl_size = os.path.getsize(ttl_path)
        json_size = os.path.getsize(json_path)

    console.print(f"  Turtle  格式: {ttl_size:,} bytes  ← 人类可读，W3C 标准")
    console.print(f"  JSON-LD 格式: {json_size:,} bytes  ← 前端友好，可嵌入 HTML")
    console.print(f"  SQL dump: 私有格式，需要 SQLite 客户端解析")

    # ── 汇总 ───────────────────────────────────────────────────────────────
    section("汇总对比")

    summary = Table(box=box.ROUNDED, title="关系型 vs 本体论存储")
    summary.add_column("维度", style="bold")
    summary.add_column("关系型（SQL）", style="red")
    summary.add_column("本体论（RDF/OWL）", style="green")
    summary.add_row("数据模型",   "表 + 外键",       "三元组 + 命名图")
    summary.add_row("Schema",    "强 Schema，DDL 变更", "无 Schema，任意扩展")
    summary.add_row("关系表达",  "JOIN 多表",        "属性路径，图遍历")
    summary.add_row("语义推断",  "无（靠代码手写）", "OWL 推理引擎自动推导")
    summary.add_row("互操作",    "SQL dump（私有）",  "Turtle/JSON-LD/RDF/XML（W3C）")
    summary.add_row("适合场景",  "结构固定，高并发 OLTP", "知识图谱，语义搜索，动态本体")
    console.print(summary)

    console.print("\n[bold green]✓ 04_comparison 完成[/]\n")


if __name__ == "__main__":
    main()
