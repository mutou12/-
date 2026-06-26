"""
示例 03：OWL-RL 推理
展示本体论最核心的"从已知推未知"能力：
  - 对称属性：单向断言 → 双向关系
  - 传递属性：多跳依赖 → 直接可达
  - 子类层次：具体类成员 → 所有上级类成员
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from rich.console import Console
from rich.table import Table
from rich import box

from src.ontology_store import OntologyStore, TKB
from src.reasoner import OntologyReasoner

console = Console()


def main():
    console.rule("[bold blue]03 · OWL-RL 推理")

    store = OntologyStore()
    store.load_all()

    reasoner = OntologyReasoner(store)

    # ── 1. 对称属性推理 ────────────────────────────────────────────────────
    console.rule("[yellow]① 对称属性推理（usedWith / competitorOf）")
    console.print(
        "原始数据中只写了 [bold]Python usedWith PyTorch[/]，\n"
        "推理引擎应自动推导出 [bold]PyTorch usedWith Python[/]"
    )

    new_sym = reasoner.explain_symmetric()
    if new_sym:
        t = Table(title="对称推导出的新三元组", box=box.SIMPLE)
        t.add_column("Subject", style="green")
        t.add_column("Predicate", style="yellow")
        t.add_column("Object", style="cyan")
        for s, p, o in new_sym:
            t.add_row(s, p, o)
        console.print(t)
    else:
        console.print("[dim]  (owlrl 已通过其他方式处理，或已存在)[/]")

    # ── 2. 传递属性推理 ────────────────────────────────────────────────────
    console.rule("[yellow]② 传递属性推理（builtOn+）")
    console.print(
        "原始: Transformers builtOn PyTorch，PyTorch(若有 builtOn)...\n"
        "SPARQL Property Path [bold]+[/] 可直接表达，owlrl 在图层面补全传递闭包"
    )

    new_trans = reasoner.explain_transitive()
    if new_trans:
        t = Table(title="传递推导出的新 builtOn 三元组", box=box.SIMPLE)
        t.add_column("Subject", style="green")
        t.add_column("Predicate", style="yellow")
        t.add_column("Object", style="cyan")
        for s, p, o in new_trans:
            t.add_row(s, p, o)
        console.print(t)
    else:
        console.print("[dim]  无新的传递三元组（当前实例链只有一跳）[/]")

    # ── 3. 类层次推理 ──────────────────────────────────────────────────────
    console.rule("[yellow]③ 子类层次推理（rdfs:subClassOf）")
    console.print(
        "PyTorch 直接类型是 [bold]MLFramework[/]，\n"
        "推理后应自动获得 [bold]Framework[/] 和 [bold]Technology[/] 成员资格"
    )

    inferred_types = reasoner.explain_class_hierarchy(TKB.PyTorch)
    if inferred_types:
        for t in inferred_types:
            label = t.split("#")[-1] if "#" in t else t
            # 只打印有意义的 tkb 命名空间类
            if "tech-kb" in t or "owl" not in t.lower():
                console.print(f"  [green]+[/] 推导出 PyTorch ∈ [bold]{label}[/]  [dim]({t})[/]")
    else:
        console.print("[dim]  无新推导类型[/]")

    # ── 4. 推理后查询对比 ──────────────────────────────────────────────────
    console.rule("[yellow]④ 推理前后查询对比：所有 Framework 实例")

    QUERY = """
    PREFIX tkb: <http://example.org/tech-kb#>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    SELECT DISTINCT ?name WHERE {
        ?x a tkb:Framework ; rdfs:label ?name .
    } ORDER BY ?name
    """

    before = {r["name"] for r in store.sparql(QUERY)}
    after  = {r["name"] for r in reasoner.run().sparql(QUERY)}
    newly  = after - before

    console.print(f"推理前 Framework 数: [bold]{len(before)}[/]  → 推理后: [bold]{len(after)}[/]")
    console.print(f"新增成员（从子类推导）: [green]{sorted(newly) or '（无，已在实例数据中声明）'}[/]")

    console.print("\n[bold green]✓ 03_reasoning 完成[/]\n")


if __name__ == "__main__":
    main()
