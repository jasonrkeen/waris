"""Missing evidence must not become benchmark observations or approval."""
from pathlib import Path
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import pandas as pd
from pandas.testing import assert_frame_equal
from offline_demo import compute_demo
from src import official_baseline_merge_review as review
from src import official_baseline_validation as validation
from src import official_baseline_merge_plan as plan
from src.utils import official_baseline_observations

ROOT = Path(__file__).resolve().parents[1]


class BenchmarkFallbackTests(unittest.TestCase):
    def test_status_notice_is_not_official_observation(self):
        notice = pd.DataFrame([{"oblast": "", "official_regional_baseline_proxy": "",
                                "latest_period": "", "source_status": "unavailable"}])
        self.assertTrue(official_baseline_observations(notice).empty)

    def test_official_observations_require_finite_positive_dated_values(self):
        frame = pd.DataFrame({"oblast": ["Kyiv"] * 5,
                              "official_regional_baseline_proxy": [12, -1, float("inf"), 9, "bad"],
                              "latest_period": ["2021", "2021", "2021", "bad", "2021"]})
        self.assertEqual(official_baseline_observations(frame).index.tolist(), [0])

    def test_valid_csv_year_survives_float_coercion_from_notice_rows(self):
        frame = pd.DataFrame({"oblast": ["Kyiv", ""],
                              "official_regional_baseline_proxy": [12, float("nan")],
                              "latest_period": [2021.0, float("nan")]})
        self.assertEqual(official_baseline_observations(frame).index.tolist(), [0])

    def test_gap_review_handles_missing_status_and_malformed_rows(self):
        fixtures = [pd.DataFrame(), pd.DataFrame([{"benchmark_status": "missing_required_inputs"}]),
                    pd.DataFrame([{"waris_oblast": "Kyiv", "official_grp_million_uah": "bad",
                                   "official_vs_synthetic_index_gap": 3,
                                   "official_to_synthetic_share_ratio": 1}])]
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "gap.csv"
            for fixture in fixtures:
                with self.subTest(columns=list(fixture)), patch.object(review, "TABLE_DIR", Path(temporary)), \
                     patch.object(review, "OFFICIAL_BASELINE_GAP_REVIEW_TABLE", output), \
                     patch.object(review, "_safe_read_csv", return_value=fixture):
                    self.assertTrue(review.build_gap_review().empty)
                    self.assertIn("review_status", pd.read_csv(output).columns)

    def test_real_benchmark_comparison_remains_available(self):
        fixture = pd.DataFrame([{"waris_oblast": "Kyiv", "official_grp_million_uah": 100,
                                 "official_vs_synthetic_index_gap": -5,
                                 "official_to_synthetic_share_ratio": 1.2}])
        with tempfile.TemporaryDirectory() as temporary, \
             patch.object(review, "TABLE_DIR", Path(temporary)), \
             patch.object(review, "OFFICIAL_BASELINE_GAP_REVIEW_TABLE", Path(temporary) / "gap.csv"), \
             patch.object(review, "_safe_read_csv", return_value=fixture):
            result = review.build_gap_review()
        self.assertEqual(len(result), 1)
        self.assertEqual(result.iloc[0].absolute_index_gap, 5)
        self.assertEqual(result.iloc[0].production_score_change, "none")

    def test_incomplete_or_failed_core_register_cannot_approve_benchmark(self):
        full = pd.DataFrame([{"check_id": f"OBV-{i:03d}", "status": "pass", "severity": "info"}
                             for i in range(1, 23)])
        failed = full.copy()
        failed.loc[failed.check_id.eq("OBV-006"), "status"] = "review_required"
        for frame in [full.iloc[:1], failed, pd.concat([full, full.iloc[:1]]), pd.DataFrame({"status": ["pass"]})]:
            self.assertEqual(validation._derive_readiness_decision(frame)["decision"], "NO_GO")
        decision = validation._derive_readiness_decision(full)
        self.assertEqual(decision["decision"], "GO_FOR_CONTROLLED_BENCHMARK_INTEGRATION")
        self.assertEqual(decision["prohibited_current_use"], "risk_layer_calculation_or_composite_scoring")

    def test_current_synthetic_baseline_takes_precedence_over_stale_scores(self):
        current = pd.DataFrame({"oblast": ["Kyiv"], "prewar_revenue_index_2021": [100]})
        stale = current.assign(prewar_revenue_index_2021=900)
        with patch.object(plan, "_safe_read_csv", side_effect=lambda path: current if path == plan.SYNTHETIC_INPUTS_RAW else stale):
            assert_frame_equal(plan._load_model_baseline(), current)


class FullFallbackPipelineTests(unittest.TestCase):
    def test_clean_and_stale_readiness_runs_with_all_provider_access_denied(self):
        runner = '''
import pathlib, runpy, sys, socket
from unittest.mock import patch
import requests
root = pathlib.Path(sys.argv[1]).resolve()
sys.path.insert(0, str(root))
sys.argv = [str(root / "main.py"), "--allow-live"]
with patch.object(requests.sessions.Session, "request", side_effect=requests.ConnectionError("Test: provider access denied")), patch.object(socket.socket, "connect", side_effect=OSError("Test: network denied")):
    runpy.run_path(str(root / "main.py"), run_name="__main__")
'''
        _, expected, expected_mc = compute_demo()
        with tempfile.TemporaryDirectory(prefix="waris_fallback_") as temporary:
            root = Path(temporary)
            shutil.copytree(ROOT / "src", root / "src", ignore=shutil.ignore_patterns("__pycache__"))
            shutil.copy2(ROOT / "main.py", root / "main.py")
            env = os.environ.copy()
            for key in ("ACLED_USERNAME", "ACLED_PASSWORD", "OPENSANCTIONS_UA_NSDC_URL"):
                env.pop(key, None)
            identities = []
            for iteration in range(2):
                if iteration:
                    pd.DataFrame([{"decision": "GO_FOR_CONTROLLED_SCORING_INTEGRATION",
                                   "approved_current_use": "scoring_integration",
                                   "prohibited_current_use": "none", "rationale": "Stale test fixture"}]).to_csv(
                        root / "outputs/tables/official_baseline_readiness_decision.csv", index=False)
                result = subprocess.run([sys.executable, "-c", runner, str(root)], cwd=root,
                                        env=env, capture_output=True, text=True, timeout=120)
                self.assertEqual(result.returncode, 0, result.stderr[-4000:])
                self.assertIn("Pipeline complete.", result.stdout)
                tables = root / "outputs/tables"
                readiness = pd.read_csv(tables / "official_baseline_readiness_decision.csv")
                self.assertEqual(readiness.iloc[0].decision, "NO_GO")
                self.assertTrue(pd.read_csv(tables / "official_baseline_gap_review.csv").empty)
                summary = pd.read_csv(tables / "official_baseline_merge_review_summary.csv").set_index("summary_area")
                self.assertEqual(summary.loc["Readiness decision", "status"], "NO_GO")
                self.assertEqual(summary.loc["Benchmark gap review", "status"], "missing")
                scored = pd.read_csv(tables / "waris_scored_oblast_sector.csv")
                columns = ["oblast", "sector", "waris_aml_review_score", "risk_band", "review_rationale"]
                assert_frame_equal(expected[columns], scored[columns], check_dtype=False)
                mc = pd.read_csv(tables / "waris_monte_carlo_results.csv")
                numeric = [c for c in expected_mc if c.startswith("mc_") or c.startswith("prob_")]
                assert_frame_equal(expected_mc[numeric], mc[numeric], check_dtype=False)
                self.assertFalse(scored.official_baseline_candidate_available.any())
                statuses = pd.read_csv(tables / "live_data_status.csv")
                official = statuses[statuses.source_name.str.contains("official baseline candidates", case=False)]
                self.assertEqual(official.iloc[0].status, "fallback")
                self.assertEqual(official.iloc[0].rows, 0)
                memo = (root / "outputs/reports/official_baseline_benchmark_review_memo.md").read_text(encoding="utf8")
                self.assertIn("decision = NO_GO", memo)
                self.assertNotIn("source-backed and unit-supported", memo)
                manifest = json.loads((root / "outputs/reports/run_manifest.json").read_text(encoding="utf8"))
                self.assertTrue(manifest["summary"]["pdf_report_exists"])
                self.assertEqual(manifest["summary"]["official_baseline_decision"], "NO_GO")
                limitations = (tables / "model_limitations_register.csv").read_text(encoding="utf8")
                self.assertNotIn("support GO for controlled benchmark integration", limitations)
                self.assertNotIn("has validated unit/scale", limitations)
                inventory = (tables / "model_inventory.csv").read_text(encoding="utf8")
                self.assertNotIn("Current approved use is controlled benchmark integration", inventory)
                self.assertIn("No benchmark approval is inferred", inventory)
                identities.append(manifest["summary"]["run_id"])
                pdf = root / "outputs/reports/waris_ukraine_aml_risk_report.pdf"
                self.assertTrue(pdf.read_bytes().startswith(b"%PDF"))
                self.assertGreater(pdf.stat().st_size, 1000)
            self.assertNotEqual(*identities)


if __name__ == "__main__":
    unittest.main()
