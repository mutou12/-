"""
示例 02：SPARQL 查询
SPARQL 对图的作用 ≈ SQL 对关系表，但天然支持路径遍历和模式匹配
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from rich.console import Console
from rich.table import Table

from src.ontology_store import OntologyStore
from src import queries as Q

console = Console()


def print_table(title: str, rows: list[dict], cols: list[str] | None = None):
    if not rows:
        console.print(f"[dim]  (无结果)[/]")
        return
    cols = cols or list(rows[0].keys())
    t = Table(title=title, show_header=True, header_style="bold magenta")
    for c in cols:
        t.add_column(c, style="cyan")
    for row in rows:
        t.add_row(*[str(row.get(c, "")) for c in cols])
    console.print(t)


def main():
    console.rule("[bold blue]02 · SPARQL 查询示例")

    store = OntologyStore()
    store.load_all()

    # Q1
    console.rule("[yellow]Q1: ML 框架列表（按 stars 排序）")
    rows = store.sparql(Q.Q_ML_FRAMEWORKS)
    print_table("ML Frameworks", rows, ["name", "stars", "releaseYear"])

    # Q2
    console.rule("[yellow]Q2: Python 生态（直接 usedWith）")
    rows = store.sparql(Q.Q_PYTHON_ECOSYSTEM)
    for r in rows:
        r["type"] = r["type"].split("#")[-1]
    print_table("Python Ecosystem", rows, ["name", "type"])

    # Q3
    console.rule("[yellow]Q3: Database 类层次与实例数")
    rows = store.sparql(Q.Q_DATABASE_HIERARCHY)
    for r in rows:
        r["subClass"] = r["subClass"].split("#")[-1]
    print_table("Database Hierarchy", rows, ["subClass", "count"])

    # Q4
    console.rule("[yellow]Q4: 竞争关系")
    rows = store.sparql(Q.Q_COMPETITORS)
    print_table("Competitors", rows, ["a_name", "b_name"])

    # Q5
    console.rule("[yellow]Q5: 从 PyTorch 出发推荐数据库（两跳遍历）")
    rows = store.sparql(Q.Q_RECOMMEND_DB)
    print_table("Recommended DBs for PyTorch", rows, ["dbName", "dbDesc"])

    # Q6
    console.rule("[yellow]Q6: License 分布统计")
    rows = store.sparql(Q.Q_LICENSE_STATS)
    print_table("License Stats", rows, ["license", "count"])

    # Q7 — 属性路径（+：一跳或多跳）
    console.rule("[yellow]Q7: Transformers 的所有 builtOn 依赖链（Property Path +）")
    rows = store.sparql(Q.Q_DEPENDENCY_CHAIN)
    print_table("Transformers Dependency Chain", rows, ["name"])

    # Q8
    console.rule("[yellow]Q8: 描述含「向量」的技术")
    rows = store.sparql(Q.Q_SEARCH_BY_DESC)
    print_table("Vector-related", rows, ["name", "desc"])

    # Q9
    console.rule("[yellow]Q9: Meta 创建的技术")
    rows = store.sparql(Q.Q_BY_CREATOR)
    for r in rows:
        r["type"] = r["type"].split("#")[-1]
    print_table("Created by Meta", rows, ["techName", "type", "year"])

    console.print("\n[bold green]✓ 02_sparql_queries 完成[/]\n")


if __name__ == "__main__":
    main()
