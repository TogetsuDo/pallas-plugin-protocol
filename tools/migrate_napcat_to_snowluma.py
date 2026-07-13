#!/usr/bin/env python3
"""NapCat → SnowLuma 批量迁移 CLI（默认不保留 NapCat 数据）。"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path


async def run(args: argparse.Namespace) -> int:
    from pallas.core.foundation.config.repo_settings import apply_repo_settings_to_environ

    apply_repo_settings_to_environ()

    from pallas.api.paths import plugin_data_dir
    from pallas_plugin_protocol.config import get_pallas_protocol_config
    from pallas_plugin_protocol.service import PallasProtocolService

    data_dir = plugin_data_dir("pallas_protocol")
    if args.data_dir:
        data_dir = Path(args.data_dir).resolve()
    cfg = get_pallas_protocol_config()
    mgr = PallasProtocolService(data_dir, cfg)
    await mgr.initialize()

    ids: list[str] | None = None
    if args.account_ids:
        ids = [x.strip() for x in args.account_ids.split(",") if x.strip()]

    result = await mgr.migrate_accounts_to_snowluma(
        ids,
        preserve_napcat_data=args.preserve_napcat_data,
        stop_napcat_containers=not args.keep_napcat_containers,
        start_after=args.start_after,
        stagger_ms=args.stagger_ms,
        max_concurrency=args.max_concurrency,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Migrate NapCat accounts to SnowLuma Docker")
    parser.add_argument(
        "--data-dir",
        help="协议数据目录（默认 Pallas data/pallas_protocol）",
    )
    parser.add_argument(
        "--account-ids",
        help="逗号分隔账号 ID；省略则迁移全部启用的 NapCat 账号",
    )
    parser.add_argument(
        "--preserve-napcat-data",
        action="store_true",
        help="保留 NapCat account_data_dir（默认使用全新 instances/<id>/snowluma）",
    )
    parser.add_argument(
        "--keep-napcat-containers",
        action="store_true",
        help="不停止/删除 NapCat Docker 容器",
    )
    parser.add_argument(
        "--start-after",
        action="store_true",
        help="迁移后以 rolling 模式批量启动 SnowLuma",
    )
    parser.add_argument("--stagger-ms", type=int, default=None, help="批量启动间隔毫秒")
    parser.add_argument(
        "--max-concurrency", type=int, default=None, help="批量启动最大并发"
    )
    args = parser.parse_args()
    try:
        return asyncio.run(run(args))
    except ValueError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 2
    except KeyboardInterrupt:
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
