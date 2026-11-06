from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import yaml
from apps.api.main import app

OPENAPI_PATH = Path("docs/api/openapi.yaml")


def _sorted(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: _sorted(value[key]) for key in sorted(value)}
    if isinstance(value, list):
        return [_sorted(item) for item in value]
    return value


def render_openapi() -> str:
    document = _sorted(app.openapi())
    return yaml.safe_dump(
        document,
        allow_unicode=True,
        default_flow_style=False,
        sort_keys=False,
        width=120,
    )


def export_openapi(path: Path = OPENAPI_PATH) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render_openapi(), encoding="utf-8", newline="\n")
    return path


def check_openapi(path: Path = OPENAPI_PATH) -> bool:
    if not path.exists():
        return False
    return path.read_text(encoding="utf-8") == render_openapi()


def main() -> None:
    parser = argparse.ArgumentParser(description="Export or verify ChronoArb OpenAPI")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--export", action="store_true", help="Write the OpenAPI export")
    group.add_argument("--check", action="store_true", help="Verify the OpenAPI export is current")
    args = parser.parse_args()

    if args.export:
        export_openapi()
        print(f"Exported {OPENAPI_PATH}")
        return

    if check_openapi():
        print(f"{OPENAPI_PATH} is up to date")
        return

    message = (
        f"{OPENAPI_PATH} is missing or out of date; run: python -m apps.api.export_openapi --export"
    )
    raise SystemExit(message)


if __name__ == "__main__":
    main()
