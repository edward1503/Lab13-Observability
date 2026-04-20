import json
import time
from pathlib import Path

import httpx

BASE_URL = "http://127.0.0.1:8000"


def get_metrics() -> dict:
    try:
        r = httpx.get(f"{BASE_URL}/metrics", timeout=5.0)
        return r.json()
    except Exception as e:
        print(f"Error fetching metrics: {e}")
        return {}


def print_dashboard():
    metrics = get_metrics()
    if not metrics:
        print("No metrics available. Start the app and send requests.")
        return

    print("\n" + "=" * 80)
    print("OBSERVABILITY DASHBOARD".center(80))
    print("=" * 80)

    print(f"\n📊 TRAFFIC & LATENCY")
    print(f"  Requests: {metrics.get('traffic', 0)}")
    print(f"  P50 Latency: {metrics.get('latency_p50', 0):.0f}ms")
    print(f"  P95 Latency: {metrics.get('latency_p95', 0):.0f}ms (SLO target: 3000ms)")
    print(f"  P99 Latency: {metrics.get('latency_p99', 0):.0f}ms")

    print(f"\n💰 COST")
    print(f"  Total Cost: ${metrics.get('total_cost_usd', 0):.6f}")
    print(f"  Avg Cost/Request: ${metrics.get('avg_cost_usd', 0):.6f}")

    print(f"\n📝 TOKENS")
    print(f"  Total Tokens In: {metrics.get('tokens_in_total', 0):,}")
    print(f"  Total Tokens Out: {metrics.get('tokens_out_total', 0):,}")

    print(f"\n⭐ QUALITY")
    print(f"  Avg Quality Score: {metrics.get('quality_avg', 0):.2f}/1.0")

    errors = metrics.get("error_breakdown", {})
    if errors:
        print(f"\n❌ ERRORS")
        for error_type, count in errors.items():
            print(f"  {error_type}: {count}")
    else:
        print(f"\n✓ No errors")

    print("\n" + "=" * 80)


def main():
    print("Dashboard refreshing every 5s... (Ctrl+C to stop)\n")
    try:
        while True:
            print_dashboard()
            time.sleep(5)
    except KeyboardInterrupt:
        print("\n\nDashboard stopped.")


if __name__ == "__main__":
    main()
