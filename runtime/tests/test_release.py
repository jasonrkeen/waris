import unittest
from unittest.mock import patch
import pandas as pd
from pandas.testing import assert_frame_equal
from offline_demo import compute_demo
from src import risk_model, monte_carlo, config


class ReleaseTests(unittest.TestCase):
    def test_repeatable_synthetic_pipeline(self):
        a = compute_demo()
        b = compute_demo()
        for x, y in zip(a, b):
            assert_frame_equal(x, y)
        scored, mc = a[1:]
        self.assertTrue(scored.waris_aml_review_score.between(0, 100).all())
        self.assertFalse(scored.duplicated(["oblast", "sector"]).any())
        self.assertTrue((mc.mc_p05_score <= mc.mc_mean_score).all())
        self.assertTrue((mc.mc_mean_score <= mc.mc_p95_score).all())
        self.assertAlmostEqual(sum(config.BASE_WEIGHTS.values()), 1.0)

    def test_official_baseline_cannot_change_score_or_simulation(self):
        raw, baseline, base_mc = compute_demo()
        context = pd.DataFrame({"oblast": raw.oblast.unique(), "official_baseline_proxy": 1e15,
                                "official_baseline_candidate_available": True,
                                "official_baseline_used_in_scoring": False})
        with patch.object(risk_model, "_load_official_baseline_candidates", return_value=context):
            changed = risk_model.calculate_risk_layers(raw)
        cols = ["oblast", "sector", "waris_aml_review_score", "risk_band", "review_rationale", *config.BASE_WEIGHTS]
        assert_frame_equal(baseline[cols], changed[cols])
        simulation = monte_carlo.run_monte_carlo(changed)
        numeric = [c for c in base_mc if c.startswith("mc_") or c.startswith("prob_")]
        assert_frame_equal(base_mc[numeric], simulation[numeric])

    def test_missing_required_input_is_rejected(self):
        raw, _, _ = compute_demo()
        with self.assertRaises(ValueError):
            risk_model.calculate_risk_layers(raw.drop(columns=["current_revenue_index"]))

    def test_reference_artifacts_do_not_change_numeric_results(self):
        raw, baseline, base_mc = compute_demo()
        fixture = raw[["oblast", "sector"]].copy()
        for name, value in {
            "official_regional_baseline_proxy": 1e15,
            "procurement_review_priority_candidate": 100,
            "procurement_intensity_score": 100,
            "procurement_value_score": 100,
            "single_bid_supplier_score": 100,
            "buyer_concentration_score": 100,
            "reconstruction_emergency_score": 100,
            "current_use": "review_artifact_only",
            "prohibited_use": "direct_scoring_without_change_control",
            "production_score_change": "none",
            "used_in_waris_scoring": False,
            "used_in_monte_carlo": False,
            "control_note": "Synthetic test fixture",
            "summary_area": "Overall freshness posture",
            "status": "review_required",
            "value": "Synthetic context",
            "run_id": "synthetic-context-test",
            "model_version": "0.12.0",
        }.items():
            fixture[name] = value
        with patch.object(risk_model, "_load_optional_csv", return_value=fixture.copy()):
            changed = risk_model.calculate_risk_layers(raw)
        cols = ["oblast", "sector", "waris_aml_review_score", "risk_band", "review_rationale", *config.BASE_WEIGHTS]
        assert_frame_equal(baseline[cols], changed[cols])
        self.assertTrue(changed.expanded_prozorro_feature_candidate_available.all())
        self.assertTrue(changed.fiu_context_available.all())
        self.assertTrue(changed.wartime_aml_typology_available.all())
        with patch.object(monte_carlo, "_load_optional_csv", return_value=fixture.copy()):
            changed_mc = monte_carlo.run_monte_carlo(changed)
        numeric = [c for c in base_mc if c.startswith("mc_") or c.startswith("prob_")]
        assert_frame_equal(base_mc[numeric], changed_mc[numeric])


if __name__ == "__main__":
    unittest.main()
