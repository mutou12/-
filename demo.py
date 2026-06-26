from pathlib import Path

from ontology_storage.storage import (
    get_assets_by_team,
    get_connection,
    get_upstream_dependencies,
    init_schema,
    seed_ontology,
)


def main() -> None:
    db_path = Path("ontology_demo.db")
    conn = get_connection(db_path)
    try:
        init_schema(conn)
        seed_ontology(conn)

        team_assets = get_assets_by_team(conn, "team-core-ai")
        print("=== team-core-ai 负责的资产 ===")
        for asset, asset_type in team_assets:
            print(f"- {asset} ({asset_type})")

        print("\n=== db-user 的上游依赖 ===")
        for dep in get_upstream_dependencies(conn, "db-user"):
            print(f"- {dep}")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
