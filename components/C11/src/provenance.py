"""File evidence, not source permission, acquisition authentication or validation.

The checksum is an integrity receipt. Retain it outside the run directory for
an external anchor; an attacker able to replace both files can rewrite it.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, replace
from datetime import datetime, timezone
import hashlib
import importlib.metadata
import json
from pathlib import Path
import platform
import sys
from uuid import uuid4

import pandas as pd

from . import config

METADATA_PATHS = (
    "outputs/tables/run_manifest.csv",
    "outputs/tables/run_manifest_summary.csv",
    "outputs/reports/run_manifest.json",
    "outputs/reports/run_provenance.json",
    "outputs/reports/run_provenance.sha256",
)
SOURCE_DIRS = ("src", "tests", "docs", "tools", ".github")
SOURCE_SUFFIXES = {".py", ".md", ".txt", ".toml", ".yml", ".yaml", ".cff"}
IGNORED_PARTS = {"__pycache__", ".pytest_cache", ".git", ".venv", ".venv-1", ".ipynb_checkpoints"}


@dataclass(frozen=True)
class FileEvidence:
    path: str
    sha256: str
    bytes: int


@dataclass(frozen=True)
class RunContext:
    run_id: str
    started_at_utc: str
    source_before: tuple[FileEvidence, ...]
    data_before: tuple[FileEvidence, ...]
    artifacts_before: tuple[FileEvidence, ...]
    environment: dict
    scoring_input: dict | None = None
    simulation_input: dict | None = None


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="microseconds")


def new_run_id() -> str:
    return "waris_" + uuid4().hex


def record_file(root: Path, path: Path) -> FileEvidence:
    if path.is_symlink() or not path.resolve().is_relative_to(root.resolve()):
        raise ValueError("Provenance refuses symlinks or files outside the project")
    before = path.stat()
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    after = path.stat()
    if (before.st_size, before.st_mtime_ns) != (after.st_size, after.st_mtime_ns):
        raise RuntimeError("File changed while provenance was being recorded")
    return FileEvidence(path.relative_to(root).as_posix(), digest.hexdigest(), after.st_size)


def eligible(path: Path) -> bool:
    return not any(p in IGNORED_PARTS for p in path.parts) and not (
        path.name == ".env" or path.name.startswith(".env.") or path.suffix == ".pyc"
    )


def source_snapshot(root: Path) -> tuple[FileEvidence, ...]:
    paths = [p for p in root.iterdir() if p.is_file() and eligible(p) and
             (p.suffix in SOURCE_SUFFIXES or p.name in {"LICENSE", ".gitignore", ".gitattributes", "RELEASE_MANIFEST.json", "release_specification.json"})]
    for name in SOURCE_DIRS:
        if (root / name).exists():
            paths.extend(p for p in (root / name).rglob("*") if p.is_file() and eligible(p))
    return tuple(record_file(root, p) for p in sorted(set(paths)))


def artifact_snapshot(root: Path) -> tuple[FileEvidence, ...]:
    paths = []
    for name in ("data", "outputs"):
        if (root / name).exists():
            paths.extend(p for p in (root / name).rglob("*") if p.is_file() and eligible(p)
                         and p.relative_to(root).as_posix() not in METADATA_PATHS)
    return tuple(record_file(root, p) for p in sorted(paths))


def start_run(root: Path) -> RunContext:
    files = artifact_snapshot(root)
    packages = sorted({(d.metadata["Name"], d.version) for d in importlib.metadata.distributions()})
    return RunContext(new_run_id(), utc_now(), source_snapshot(root),
                      tuple(f for f in files if f.path.startswith("data/")), files,
                      {"python": sys.version, "platform": platform.platform(),
                       "packages": [{"name": n, "version": v} for n, v in packages]})


def capture_scoring_input(context: RunContext, root: Path, frame: pd.DataFrame) -> RunContext:
    """Snapshot the ordered frame immediately before calculate_risk_layers.

    The CSV serialization is recorded, not a claim about upstream provider reads.
    It may be provider-derived: keep this generated snapshot private until cleared.
    """
    path = root / "data/processed/run_scoring_input_snapshot.csv"
    path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(path, index=False, lineterminator="\n")
    evidence = asdict(record_file(root, path))
    evidence.update(rows=len(frame), columns=list(frame.columns), serialization="pandas_csv_utf8_lf_index_false",
                    purpose="ordered_frame_passed_to_calculate_risk_layers")
    return replace(context, scoring_input=evidence)


def capture_simulation_input(context: RunContext, root: Path, frame: pd.DataFrame) -> RunContext:
    """Record the ordered scored frame passed directly to Monte Carlo."""
    path = root / "data/processed/run_simulation_input_snapshot.csv"
    path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(path, index=False, lineterminator="\n")
    evidence = asdict(record_file(root, path))
    evidence.update(rows=len(frame), columns=list(frame.columns), serialization="pandas_csv_utf8_lf_index_false",
                    purpose="ordered_frame_passed_to_run_monte_carlo")
    return replace(context, simulation_input=evidence)


def seal_run(root: Path, context: RunContext | None, run_id: str, phase: str) -> dict:
    current_source = source_snapshot(root)
    if context is not None and current_source != context.source_before:
        raise RuntimeError("Source changed during execution; final provenance refused")
    if context is not None:
        for kind, snapshot in (("scoring", context.scoring_input), ("simulation", context.simulation_input)):
            if snapshot is not None:
                current_input = asdict(record_file(root, root / snapshot["path"]))
                if any(current_input[k] != snapshot[k] for k in current_input):
                    raise RuntimeError(f"Captured {kind} input changed before finalization")
    artifacts = artifact_snapshot(root)
    manifest_payload = json.loads((root / METADATA_PATHS[2]).read_text(encoding="utf8"))
    expected_artifacts = {r["path"]: (r["sha256"], r["file_size_bytes"]) for r in manifest_payload["artifacts"]}
    if expected_artifacts != {r.path: (r.sha256, r.bytes) for r in artifacts}:
        raise RuntimeError("Artifacts changed between manifest inventory and final sealing")
    if manifest_payload["summary"]["run_id"] != run_id:
        raise ValueError("Manifest and seal execution identities differ")
    before = {f.path: f for f in context.artifacts_before} if context else {}
    payload = {
        "schema_version": 1, "run_id": run_id, "phase": phase, "sealed_at_utc": utc_now(),
        "execution_scope": "pipeline_observed_with_scoring_frame_snapshot" if context else "standalone_file_observation_not_pipeline_execution",
        "context": asdict(context) if context else None,
        "source_final": [asdict(f) for f in current_source],
        "artifacts_final": [dict(asdict(f), observation=("preexisting_content_unchanged" if before.get(f.path) == f
                              else "preexisting_content_changed" if f.path in before else "new_path_observed")) for f in artifacts],
        "manifest_files": [asdict(record_file(root, root / p)) for p in METADATA_PATHS[:3]],
        "inventory_exclusions": list(METADATA_PATHS),
        "secret_file_policy": "credential files and cache paths excluded; no environment values captured",
        "parameters": {"model_version": config.MODEL_VERSION, "acquisition_policy_version": config.ACQUISITION_POLICY_VERSION,
                       "random_seed": config.RANDOM_SEED, "monte_carlo_runs": config.MONTE_CARLO_RUNS,
                       "weights": config.BASE_WEIGHTS, "risk_bands": config.RISK_BANDS},
        "boundaries": {"official_grp": "benchmark_only", "expanded_prozorro": "review_only",
                       "fiu": "national_context_only_unverified_claims_excluded", "wartime_typologies": "literature_reference_only"},
        "limitations": ["File observation does not prove that every file was consumed or produced by this run.",
                        "Preexisting unchanged content is not asserted to be freshly regenerated.",
                        "Snapshots do not authenticate provider acquisition, permissions or data quality.",
                        "Paths and hashes can be sensitive; this receipt is private until cleared.",
                        "The PDF contains pre-report metadata; final inventory and seal are external to the PDF."],
    }
    path = root / METADATA_PATHS[3]
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf8")
    (root / METADATA_PATHS[4]).write_text(record_file(root, path).sha256 + "  run_provenance.json\n", encoding="utf8")
    return payload


def verify_run(root: Path) -> list[str]:
    """Return integrity errors without printing source data or credential values."""
    errors = []
    try:
        path = root / METADATA_PATHS[3]
        expected = (root / METADATA_PATHS[4]).read_text(encoding="utf8").split()[0]
        if record_file(root, path).sha256 != expected:
            return ["seal_checksum_mismatch"]
        payload = json.loads(path.read_text(encoding="utf8"))
        current = {f.path: asdict(f) for f in artifact_snapshot(root)}
        recorded = {f["path"]: {k: f[k] for k in ("path", "sha256", "bytes")} for f in payload["artifacts_final"]}
        if current != recorded:
            errors.append("artifact_inventory_or_content_mismatch")
        if [asdict(f) for f in source_snapshot(root)] != payload["source_final"]:
            errors.append("source_inventory_or_content_mismatch")
        for row in payload["manifest_files"]:
            if asdict(record_file(root, root / row["path"])) != row:
                errors.append("manifest_content_mismatch")
        manifest = json.loads((root / METADATA_PATHS[2]).read_text(encoding="utf8"))
        manifest_artifacts = {r["path"]: (r["sha256"], r["file_size_bytes"]) for r in manifest["artifacts"]}
        if manifest_artifacts != {r["path"]: (r["sha256"], r["bytes"]) for r in payload["artifacts_final"]}:
            errors.append("manifest_and_seal_inventory_mismatch")
        if manifest["summary"]["run_id"] != payload["run_id"]:
            errors.append("run_identity_mismatch")
        if payload["context"] and payload["context"]["run_id"] != payload["run_id"]:
            errors.append("context_identity_mismatch")
    except (OSError, ValueError, KeyError, TypeError, IndexError):
        errors.append("missing_or_invalid_provenance")
    return errors


def main() -> None:
    import argparse
    parser = argparse.ArgumentParser(description="Verify a local WARIS provenance seal; no provider access.")
    parser.add_argument("--verify", action="store_true", required=True)
    parser.add_argument("--root", type=Path, default=config.BASE_DIR)
    args = parser.parse_args()
    errors = verify_run(args.root.resolve())
    print(json.dumps({"integrity_errors": errors, "status": "failed" if errors else "passed"}))
    raise SystemExit(1 if errors else 0)


if __name__ == "__main__":
    main()
