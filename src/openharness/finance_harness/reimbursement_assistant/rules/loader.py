"""Safe YAML loading for external source manifests and rule packs."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast

import yaml
from pydantic import ValidationError

from .models import (
    ScenarioRulePack,
    SourceManifest,
)
from .validators import (
    RuleValidationReport,
    assert_publishable,
    validate_rule_pack,
    validate_rule_pack_set,
)
from ..schemas import RulePackVersion


_MAX_YAML_BYTES = 2_000_000
_YAML_SUFFIXES = {".yaml", ".yml"}


class RulePackLoadError(ValueError):
    """Raised for unsafe files, malformed YAML, or invalid rule data."""


@dataclass(frozen=True)
class LoadedRulePack:
    """Validated rule data plus its exact file identity and validation report."""

    pack: ScenarioRulePack
    version: RulePackVersion
    validation: RuleValidationReport
    path: Path


def _read_yaml_mapping(path: Path) -> tuple[dict[str, Any], str]:
    if path.suffix.lower() not in _YAML_SUFFIXES:
        raise RulePackLoadError(f"rule data must be YAML: {path}")
    if path.is_symlink():
        raise RulePackLoadError(f"symbolic links are not accepted for rule data: {path}")
    try:
        raw = path.read_bytes()
    except OSError as exc:
        raise RulePackLoadError(f"cannot read rule data {path}: {exc}") from exc
    if len(raw) > _MAX_YAML_BYTES:
        raise RulePackLoadError(f"rule data exceeds {_MAX_YAML_BYTES} bytes: {path}")
    checksum = f"sha256:{hashlib.sha256(raw).hexdigest()}"
    try:
        parsed = yaml.safe_load(raw.decode("utf-8"))
    except (UnicodeDecodeError, yaml.YAMLError) as exc:
        raise RulePackLoadError(f"invalid safe YAML in {path}: {exc}") from exc
    if not isinstance(parsed, dict):
        raise RulePackLoadError(f"top-level YAML value must be a mapping: {path}")
    return cast(dict[str, Any], parsed), checksum


def load_source_manifest(path: str | Path) -> SourceManifest:
    """Load and validate a source manifest without resolving private documents."""

    manifest_path = Path(path)
    payload, _ = _read_yaml_mapping(manifest_path)
    try:
        return SourceManifest.model_validate(payload)
    except ValidationError as exc:
        raise RulePackLoadError(f"invalid source manifest {manifest_path}: {exc}") from exc


def load_rule_pack(
    path: str | Path,
    manifest: SourceManifest,
    *,
    require_publishable: bool = False,
) -> LoadedRulePack:
    """Load one pack, verify every source, and optionally enforce activation gates."""

    rule_path = Path(path)
    payload, checksum = _read_yaml_mapping(rule_path)
    try:
        pack = ScenarioRulePack.model_validate(payload)
    except ValidationError as exc:
        raise RulePackLoadError(f"invalid rule pack {rule_path}: {exc}") from exc

    validation = validate_rule_pack(pack, manifest)
    if not validation.is_valid:
        raise RulePackLoadError(
            f"rule pack integrity check failed for {rule_path}: " + "; ".join(validation.errors)
        )
    if require_publishable:
        assert_publishable(validation)

    version = RulePackVersion(
        rule_pack_id=pack.rule_pack_id,
        scene_id=pack.scene_id,
        version=pack.version,
        status=pack.status,
        content_checksum=checksum,
        source_document_ids=list(pack.source_document_ids()),
    )
    return LoadedRulePack(
        pack=pack,
        version=version,
        validation=validation,
        path=rule_path,
    )


def load_rule_packs(
    directory: str | Path,
    manifest: SourceManifest,
    *,
    require_publishable: bool = False,
) -> tuple[LoadedRulePack, ...]:
    """Load a deterministic directory snapshot and reject cross-pack conflicts."""

    root = Path(directory)
    if not root.is_dir():
        raise RulePackLoadError(f"rule pack directory does not exist: {root}")
    paths = tuple(sorted((*root.glob("*.yaml"), *root.glob("*.yml"))))
    if not paths:
        raise RulePackLoadError(f"rule pack directory contains no YAML files: {root}")
    loaded = tuple(
        load_rule_pack(path, manifest, require_publishable=require_publishable)
        for path in paths
    )
    set_report = validate_rule_pack_set(tuple(item.pack for item in loaded))
    if not set_report.is_valid:
        raise RulePackLoadError("rule pack set validation failed: " + "; ".join(set_report.errors))
    if require_publishable:
        assert_publishable(set_report)
    return loaded
