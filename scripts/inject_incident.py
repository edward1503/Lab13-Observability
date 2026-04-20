from __future__ import annotations

import argparse

import httpx

BASE_URL = "http://127.0.0.1:8000"
SCENARIOS = ("rag_slow", "tool_fail", "cost_spike")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--scenario", choices=SCENARIOS)
    parser.add_argument("--disable", action="store_true")
    parser.add_argument("--status", action="store_true", help="Show current incident state")
    parser.add_argument("--base-url", default=BASE_URL, help="FastAPI base URL")
    return parser


def build_incident_path(scenario: str | None, disable: bool, status: bool) -> str:
    if status:
        return "/health"
    if scenario not in SCENARIOS:
        raise ValueError(f"Unknown incident: {scenario}")
    action = "disable" if disable else "enable"
    return f"/incidents/{scenario}/{action}"


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    if not args.status and not args.scenario:
        parser.error("--scenario is required unless --status is used")

    path = build_incident_path(args.scenario, args.disable, args.status)
    if args.status:
        r = httpx.get(f"{args.base_url}{path}", timeout=10.0)
    else:
        r = httpx.post(f"{args.base_url}{path}", timeout=10.0)
    print(r.status_code, r.json())


if __name__ == "__main__":
    main()
