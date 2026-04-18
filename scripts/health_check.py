"""
Pramaan — Health Check Script

Checks all model services and the gateway.

Usage:
    python scripts/health_check.py
    python scripts/health_check.py --gateway http://localhost:8000
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import httpx

ROOT = Path(__file__).parent.parent
CONFIG_PATH = ROOT / "config" / "pramaan_config.json"


def check(name: str, url: str, timeout: int = 5) -> bool:
    try:
        resp = httpx.get(f"{url}/health", timeout=timeout)
        data = resp.json()
        status = data.get("status", "?")
        loaded = data.get("model_loaded", "?")
        ok = resp.status_code == 200 and status == "ok"
        symbol = "✅" if ok else "❌"
        print(f"  {symbol} {name:30s}  status={status}  loaded={loaded}  [{url}]")
        return ok
    except Exception as exc:
        print(f"  ❌ {name:30s}  UNREACHABLE  [{url}]  ({exc})")
        return False


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--gateway", default="http://localhost:8000")
    parser.add_argument("--timeout", type=int, default=5)
    args = parser.parse_args()

    with open(CONFIG_PATH) as f:
        config = json.load(f)

    print("\n🔍 Pramaan Health Check\n")
    print("  Gateway:")
    gw_ok = check("gateway", args.gateway, args.timeout)

    print("\n  Model Services:")
    results = []
    for model in config["models"]:
        if not model.get("enabled", True):
            print(f"  ⏭️  {model['name']:30s}  disabled")
            continue
        # For local testing, replace docker hostname with localhost
        url = model["url"].replace(f"http://{model['name']}", "http://localhost")
        ok = check(model["name"], url, args.timeout)
        results.append(ok)

    print()
    all_ok = gw_ok and all(results)
    if all_ok:
        print("✅ All services healthy!")
    else:
        print("❌ Some services are unhealthy. Run `make start` to bring them up.")
        sys.exit(1)


if __name__ == "__main__":
    main()
