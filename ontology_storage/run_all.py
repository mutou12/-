"""
一键运行所有示例
"""
import subprocess, sys

scripts = [
    ("01 基础 CRUD",     "examples/01_basic_crud.py"),
    ("02 SPARQL 查询",   "examples/02_sparql_queries.py"),
    ("03 OWL-RL 推理",   "examples/03_reasoning.py"),
    ("04 关系型 vs 本体论", "examples/04_comparison.py"),
]

for title, path in scripts:
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")
    ret = subprocess.run([sys.executable, path])
    if ret.returncode != 0:
        print(f"\n[FAIL] {path} exited with code {ret.returncode}")
        sys.exit(1)

print("\n✓ 全部示例运行完毕")
