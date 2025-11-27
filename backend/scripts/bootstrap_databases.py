"""CLI utility to create the four asset databases and core tables."""

from __future__ import annotations

import argparse

from db import (
    DatabaseBootstrapper,
    DatabaseSettings,
    get_asset_databases,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Bootstrap per-asset Postgres databases."
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the plan without creating databases or tables.",
    )
    parser.add_argument(
        "--skip-tables",
        action="store_true",
        help="Create databases only; skip running CREATE TABLE statements.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    settings = DatabaseSettings.from_env()
    targets = get_asset_databases(settings.app_prefix)

    print("Asset databases:")
    for asset_class, db_name in targets.items():
        print(f"  - {asset_class}: {db_name}")

    if args.dry_run:
        print("Dry run enabled, exiting without changes.")
        return

    bootstrapper = DatabaseBootstrapper(settings)
    bootstrapper.bootstrap(create_tables=not args.skip_tables)
    print("Bootstrap complete.")


if __name__ == "__main__":
    main()
