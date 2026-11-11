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
    def test_controlled_live_pipeline_stops_at_ACLED_gate_with_provider_access_denied(self):
        runner = """
import pathlib, runpy, sys, socket
from unittest.mock import patch
import requests
root=pathlib.Path(sys.argv[1]).resolve()
sys.path.insert(0,str(root));sys.argv=[str(root/'main.py'),'--allow-live']
with patch.object(requests.sessions.Session,'request',side_effect=requests.ConnectionError('Test provider access denied')),patch.object(socket.socket,'connect',side_effect=OSError('Test network denied')):
    runpy.run_path(str(root/'main.py'),run_name='__main__')
"""
        with tempfile.TemporaryDirectory(prefix='waris_controlled_gate_') as temporary:
            root=Path(temporary)
            shutil.copytree(ROOT/'src',root/'src',ignore=shutil.ignore_patterns('__pycache__'))
            shutil.copy2(ROOT/'main.py',root/'main.py')
            env=os.environ.copy()
            for key in ('ACLED_USERNAME','ACLED_PASSWORD','OPENSANCTIONS_UA_NSDC_URL'):env.pop(key,None)
            (root/'outputs/tables').mkdir(parents=True)
            for iteration in range(2):
                if iteration:
                    pd.DataFrame([dict(decision='GO_FOR_CONTROLLED_SCORING_INTEGRATION',approved_current_use='scoring_integration',prohibited_current_use='none')]).to_csv(root/'outputs/tables/official_baseline_readiness_decision.csv',index=False)
                result=subprocess.run([sys.executable,'-c',runner,str(root)],cwd=root,env=env,capture_output=True,text=True,timeout=120)
                self.assertNotEqual(result.returncode,0)
                self.assertIn('ACLED acquisition and cache enrichment held',result.stderr)
                self.assertFalse((root/'outputs/tables/waris_scored_oblast_sector.csv').exists())



if __name__ == "__main__":
    unittest.main()
