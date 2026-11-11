"""Network-free, synthetic-only demonstration; never reads local provider data."""
from contextlib import ExitStack
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
import hashlib
import importlib.metadata
import json
import platform
import socket

from src import config, data_collection, risk_model, monte_carlo

ROOT = Path(__file__).resolve().parent


def compute_demo():
    # Redirect every module-level artifact path to an empty private directory.
    # This prevents historical/source-backed context from entering the demo.
    with TemporaryDirectory() as temporary, ExitStack() as stack:
        scratch = Path(temporary)
        for module in (config, data_collection, risk_model, monte_carlo):
            for name, value in list(vars(module).items()):
                if isinstance(value, Path) and value.is_relative_to(ROOT):
                    stack.enter_context(patch.object(module, name, scratch / value.relative_to(ROOT)))
        stack.enter_context(patch.object(socket.socket, "connect", side_effect=RuntimeError("Network prohibited in synthetic demo")))
        raw = data_collection.build_synthetic_oblast_sector_data()
        scored = risk_model.calculate_risk_layers(raw)
        mc = monte_carlo.run_monte_carlo(scored)
        return raw, scored, mc


def main():
    raw, scored, mc = compute_demo()
    tables = ROOT / "outputs" / "tables"
    tables.mkdir(parents=True, exist_ok=True)
    frames = {
        "synthetic_inputs.csv": raw,
        "waris_scored_oblast_sector.csv": scored,
        "waris_oblast_summary.csv": risk_model.summarize_by_oblast(scored),
        "waris_sector_summary.csv": risk_model.summarize_by_sector(scored),
        "waris_monte_carlo_results.csv": mc,
    }
    manifest = {
        "release_candidate": "0.12.0-rc13-methodology-review", "model_version": config.MODEL_VERSION,
        "data_mode": "synthetic_only", "network_allowed": False,
        "official_grp_posture": "benchmark_only", "random_seed": config.RANDOM_SEED,
        "monte_carlo_runs": config.MONTE_CARLO_RUNS,
        "python": platform.python_version(),
        "dependencies": {n: importlib.metadata.version(n) for n in ("pandas", "numpy", "streamlit", "reportlab", "requests", "matplotlib", "python-dotenv")},
        "files": {},
    }
    for name, frame in frames.items():
        frame = frame.copy()
        frame["data_mode"] = "synthetic_only"
        path = tables / name
        frame.to_csv(path, index=False, lineterminator="\n")
        manifest["files"][name] = {"rows": len(frame), "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
    report_dir = ROOT / "outputs" / "reports"
    report_dir.mkdir(parents=True, exist_ok=True)
    (report_dir / "synthetic_demo_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf8")
    print(f"Synthetic-only demonstration complete: {len(scored)} rows. No provider downloads or historical inputs used.")


if __name__ == "__main__":
    main()

