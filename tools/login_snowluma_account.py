#!/usr/bin/env python3
"""一键登录测试机 3879348674：恢复 QQ 登录 → consent → inject hook。"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

import httpx

BOT_ROOT = Path(__file__).resolve().parents[2] / "Pallas-Bot"
PROTO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROTO_ROOT / "src"))


async def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--account-id", default="3879348674")
    parser.add_argument(
        "--protocol-base",
        default="http://127.0.0.1:7969/pallas/protocol/console",
    )
    parser.add_argument("--token", default="")
    args = parser.parse_args()

    headers: dict[str, str] = {}
    if args.token.strip():
        headers["X-Pallas-Protocol-Token"] = args.token.strip()

    base = args.protocol_base.rstrip("/")
    account_id = args.account_id.strip()
    timeout = httpx.Timeout(60.0, connect=10.0)

    async with httpx.AsyncClient(timeout=timeout, headers=headers) as client:
        print(f"[1/3] 恢复登录 POST {base}/api/accounts/{account_id}/qrcode/refresh")
        rr = await client.post(f"{base}/api/accounts/{account_id}/qrcode/refresh")
        rr.raise_for_status()
        refresh = rr.json()
        print(json.dumps(refresh, ensure_ascii=False, indent=2))

        await asyncio.sleep(5)

        print(f"[2/3] 注入 Hook POST .../snowluma/inject-hook")
        ir = await client.post(
            f"{base}/api/accounts/{account_id}/snowluma/inject-hook"
        )
        if ir.status_code >= 400:
            print(ir.text)
            ir.raise_for_status()
        inject = ir.json()
        print(json.dumps(inject, ensure_ascii=False, indent=2))

        print(f"[3/3] 查询账号状态 GET .../api/accounts/{account_id}")
        ar = await client.get(f"{base}/api/accounts/{account_id}")
        ar.raise_for_status()
        acc = ar.json().get("account") or {}
        print(
            f"connected={acc.get('connected')} process_running={acc.get('process_running')} pid={acc.get('pid')}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
