import unittest
from tempfile import TemporaryDirectory
from pathlib import Path
from unittest.mock import patch

from src import fiu_official_context as fiu, reference_evidence as evidence


class ReferenceEvidenceTests(unittest.TestCase):
    def test_quarterly_values_and_source_locators_match_recorded_review(self):
        with TemporaryDirectory() as directory:
            with patch.object(fiu, "FIU_REPORTING_STATISTICS_CONTEXT_TABLE", Path(directory)/"stats.csv"), patch.object(fiu, "FIU_CASE_REFERRAL_CONTEXT_TABLE", Path(directory)/"referrals.csv"):
                stats = fiu.build_fiu_reporting_statistics_context()
                referrals = fiu.build_fiu_case_referral_context()
        self.assertEqual(len(stats), 12)
        self.assertEqual(len(referrals), 10)
        self.assertTrue(stats.reference_verification_status.eq(evidence.NUMERIC_CHECKED).all())
        self.assertTrue(referrals.reference_verification_status.eq(evidence.NUMERIC_CHECKED).all())
        self.assertTrue(stats.source_url.eq(evidence.STATS_URL).all())
        self.assertNotIn("FIU-STAT-006", set(stats.metric_id))
        import pandas as pd
        internal = evidence.annotate_fiu_statistics(pd.DataFrame([r.__dict__ for r in fiu._reporting_statistics_rows()]))
        self.assertEqual(len(internal), 13)
        self.assertEqual(internal.loc[internal.metric_id.eq("FIU-STAT-006"), "semantic_review_status"].item(), "label_and_denominator_require_review")
        self.assertFalse(stats.used_in_waris_scoring.any())
        self.assertFalse(referrals.used_in_monte_carlo.any())

    def test_changed_or_unknown_values_do_not_inherit_verification(self):
        import pandas as pd
        frame=pd.DataFrame([{"metric_id":"FIU-STAT-001","metric_value":-1}, {"metric_id":"unknown","metric_value":448075}])
        result=evidence.annotate_fiu_statistics(frame)
        self.assertEqual(result.reference_verification_status.tolist(), ["value_mismatch_requires_review", evidence.UNVERIFIED])

    def test_annual_report_and_mixed_claims_remain_unverified(self):
        import pandas as pd
        sources=evidence.annotate_fiu_sources(pd.DataFrame([r.__dict__ for r in fiu._source_register_rows()]))
        annual=sources.loc[sources.source_id.eq("FIU-SRC-003")].iloc[0]
        self.assertEqual(annual.reference_verification_status,evidence.UNVERIFIED)
        typologies=evidence.annotate_fiu_typologies(pd.DataFrame([r.__dict__ for r in fiu._typology_support_rows()]))
        self.assertIn("unverified",typologies.loc[typologies.typology_support_id.eq("FIU-TYP-002"),"reference_verification_status"].item())
        self.assertFalse(typologies.used_in_waris_scoring.any())


if __name__ == "__main__":
    unittest.main()
