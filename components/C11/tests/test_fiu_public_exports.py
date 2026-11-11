"""Gate exported context before bridges, summaries, charts and presentation."""
import pandas as pd

from src import data_collection, fiu_official_context as fiu


def test_exported_context_contains_only_checked_rows_and_source_documents(tmp_path, monkeypatch):
    monkeypatch.setattr(fiu, "TABLE_DIR", tmp_path)
    paths = {
        "FIU_SOURCE_REGISTER_TABLE": "sources.csv",
        "FIU_REPORTING_STATISTICS_CONTEXT_TABLE": "statistics.csv",
        "FIU_CASE_REFERRAL_CONTEXT_TABLE": "referrals.csv",
        "FIU_TYPOLOGY_SUPPORT_REGISTER_TABLE": "typologies.csv",
        "FIU_CONTEXT_SUMMARY_TABLE": "summary.csv",
    }
    for key, filename in paths.items():
        monkeypatch.setattr(fiu, key, tmp_path / filename)
    tables = fiu.build_fiu_official_context_artifacts()
    assert tables["source_register"].source_id.tolist() == ["FIU-SRC-001", "FIU-SRC-002"]
    assert len(tables["reporting_statistics_context"]) == 12
    assert len(tables["case_referral_context"]) == 10
    assert tables["typology_support_register"].typology_support_id.tolist() == ["FIU-TYP-006"]
    assert len(fiu._typology_support_rows()) == 7  # Internal audit definitions preserved.
    assert pd.read_csv(tmp_path / "typologies.csv").typology_support_id.tolist() == ["FIU-TYP-006"]
    summary = (tmp_path / "summary.csv").read_text(encoding="utf8")
    for unsupported in ("war_and_terrorism_financing", "budget_and_state_assets", "fraud_proceeds_laundering"):
        assert unsupported not in summary


def test_alignment_crosswalk_excludes_unverified_annual_themes(tmp_path, monkeypatch):
    monkeypatch.setattr(data_collection, "RAW_DIR", tmp_path / "raw")
    monkeypatch.setattr(data_collection, "TABLE_DIR", tmp_path / "tables")
    frame = data_collection.build_fiu_context_layer_alignment_crosswalk()
    assert set(frame.reference_theme) == {"financial_transaction_reporting_statistics", "nabu_case_referral_context"}
    assert frame.production_score_change.eq("none").all()
    assert frame.current_use_in_scoring.eq("not_a_scoring_field").all()
