#!/usr/bin/env python3
"""Validate reimbursement source provenance and candidate rule packs."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from openharness.finance_harness.reimbursement_assistant.rules import (  # type: ignore[import-untyped]
    RulePackLoadError,
    load_rule_packs,
    load_source_manifest,
)


REPO_ROOT = Path(__file__).parents[2]
DEFAULT_ROOT = REPO_ROOT / "configs" / "finance" / "reimbursement_assistant"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--manifest",
        type=Path,
        default=DEFAULT_ROOT / "source_manifest.yaml",
        help="source manifest YAML",
    )
    parser.add_argument(
        "--rule-pack-root",
        type=Path,
        default=DEFAULT_ROOT / "rule_packs",
        help="directory containing candidate rule packs",
    )
    parser.add_argument(
        "--require-publishable",
        action="store_true",
        help="fail until every pack and source has passed human activation gates",
    )
    parser.add_argument("--json", action="store_true", help="emit a JSON summary")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        manifest = load_source_manifest(args.manifest)
        loaded = load_rule_packs(args.rule_pack_root, manifest)
    except RulePackLoadError as exc:
        print(f"INVALID: {exc}")
        return 1

    summaries = [
        {
            "scene_id": item.pack.scene_id,
            "rule_pack_id": item.pack.rule_pack_id,
            "status": item.pack.status.value,
            "rule_count": len(item.pack.rules),
            "valid": item.validation.is_valid,
            "publishable": item.validation.is_publishable,
            "publish_blockers": list(item.validation.publish_blockers),
            "content_checksum": item.version.content_checksum,
        }
        for item in loaded
    ]
    if args.json:
        print(json.dumps({"manifest": manifest.manifest_id, "packs": summaries}, ensure_ascii=False))
    else:
        print(f"Manifest: {manifest.manifest_id}@{manifest.version}")
        for summary in summaries:
            print(
                f"VALID {summary['scene_id']}: {summary['rule_count']} rules, "
                f"status={summary['status']}, publishable={summary['publishable']}"
            )
            for blocker in summary["publish_blockers"]:
                print(f"  REVIEW: {blocker}")

    if args.require_publishable and any(not item["publishable"] for item in summaries):
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
