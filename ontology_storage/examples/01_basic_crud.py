"""
示例 01：基础 CRUD 操作
展示三元组存储的增删改查，对比 SQL 的 INSERT/UPDATE/DELETE
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rdflib.namespace import RDF, RDFS, XSD
from rdflib import Literal

from src.ontology_store import OntologyStore, TKB

console = Console()


def main():
    console.rule("[bold blue]01 · 基础 CRUD 操作")

    store = OntologyStore()
    store.load_all()
    console.print(f"\n[green]✓ 加载完成[/]  初始三元组数: {store.stats()['triples']}")

    # ── CREATE ─────────────────────────────────────────────────────────────
    console.rule("[yellow]CREATE — 添加新技术实体")

    langchain_uri = store.add_entity(
        name="LangChain",
        class_uri=TKB.Framework,
        label="LangChain",
        releaseYear=2022,
        license="MIT",
        githubStars=90000,
        description="LLM 应用编排框架",
    )
    store.add_relation(langchain_uri, TKB.primaryLanguage, TKB.Python)
    store.add_relation(langchain_uri, TKB.usedWith, TKB.Transformers)
    store.add_relation(langchain_uri, TKB.usedWith, TKB.Chroma)

    console.print(f"[green]✓ 添加 LangChain[/]  当前三元组数: {store.stats()['triples']}")

    # ── READ ───────────────────────────────────────────────────────────────
    console.rule("[yellow]READ — 读取实体完整信息")

    info = store.get_entity_info(langchain_uri)

    t = Table(title="LangChain 实体信息", show_header=True)
    t.add_column("字段", style="cyan")
    t.add_column("值")
    t.add_row("URI", info["uri"])
    t.add_row("类型", str(info["types"]))
    for k, v in info["properties"].items():
        t.add_row(k, str(v))
    for k, v in info["relations"].items():
        t.add_row(k, "\n".join(str(x).split("#")[-1] for x in v))
    console.print(t)

    # ── UPDATE ─────────────────────────────────────────────────────────────
    console.rule("[yellow]UPDATE — 更新数据属性")

    store.update_data_property(langchain_uri, TKB.githubStars, 95000, XSD.integer)
    updated = store.get_entity_info(langchain_uri)
    console.print(f"[green]✓ githubStars 更新为: {updated['properties'].get('githubStars')}")

    # ── DELETE ─────────────────────────────────────────────────────────────
    console.rule("[yellow]DELETE — 删除实体")

    # 先建一个临时实体再删
    tmp = store.add_entity("TmpTech", TKB.Technology, "Temporary Tech")
    before = store.stats()["triples"]
    removed = store.remove_entity(tmp)
    after = store.stats()["triples"]
    console.print(f"[green]✓ 删除临时实体[/]  移除三元组: {removed}  {before} → {after}")

    # ── 图统计 ─────────────────────────────────────────────────────────────
    console.rule("[yellow]图统计")
    stats = store.stats()
    for k, v in stats.items():
        console.print(f"  {k}: [bold]{v}[/]")

    console.print("\n[bold green]✓ 01_basic_crud 完成[/]\n")


if __name__ == "__main__":
    main()
