from pathlib import Path
import os
import tempfile
import unittest
from unittest.mock import Mock, patch

from src import live_data, config


class NBUQueryTests(unittest.TestCase):
    def test_documented_monthly_queries_and_date_only_loan(self):
        calls = {}

        def response_for(url, **kwargs):
            endpoint = url.rsplit("/", 1)[-1]
            calls[endpoint] = kwargs["params"].copy()
            response = Mock(status_code=200)
            response.json.return_value = [{"value": 1, "date": "20240101"}]
            return response

        with tempfile.TemporaryDirectory() as temporary, \
             patch.object(live_data, "RAW_DIR", Path(temporary)), \
             patch.dict(os.environ, {"NBU_REPORT_DATE": "20240101"}), \
             patch.object(live_data.requests, "get", side_effect=response_for):
            datasets, status = live_data.fetch_nbu_financial_context()
            self.assertEqual(status.status, "live")
            self.assertEqual(status.rows, 3)
            self.assertEqual(len(datasets), 3)
            self.assertEqual(set(calls), {"basindbank", "banksincexp", "loan"})
            self.assertEqual(calls["basindbank"]["period"], "m")
            self.assertEqual(calls["banksincexp"]["period"], "m")
            self.assertNotIn("period", calls["loan"])
            self.assertTrue(all(c["date"] == "20240101" for c in calls.values()))
            self.assertIn("nbu-query-repair-1", config.ACQUISITION_POLICY_VERSION.split("+"))

    def test_error_payloads_do_not_count_as_working_datasets(self):
        response = Mock(status_code=200)
        response.json.return_value = {"message": "Unavailable dataset"}
        with tempfile.TemporaryDirectory() as temporary, \
             patch.object(live_data, "RAW_DIR", Path(temporary)), \
             patch.object(live_data.requests, "get", return_value=response):
            datasets, status = live_data.fetch_nbu_financial_context()
            self.assertIsNone(datasets)
            self.assertEqual(status.status, "fallback")
            self.assertEqual(status.rows, 0)


if __name__ == "__main__":
    unittest.main()
