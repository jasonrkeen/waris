"""Presentation must not promote unchecked references into public claims."""
import pandas as pd
import pytest
from pandas.testing import assert_frame_equal
from reportlab.lib.styles import getSampleStyleSheet

from src import fiu_official_context as fiu, reference_evidence as evidence
from src import report_generator


def test_fiu_public_selection_keeps_checked_rows_and_preserves_internal_records():
    stats = evidence.annotate_fiu_statistics(pd.DataFrame([r.__dict__ for r in fiu._reporting_statistics_rows()]))
    original = stats.copy(deep=True)
    selected = evidence.select_fiu_public_context(stats, "statistics")
    assert len(selected.frame) == 12
    assert selected.withheld_rows == 1
    assert "FIU-STAT-006" not in set(selected.frame.metric_id)
    assert_frame_equal(stats, original)


@pytest.mark.parametrize("mutation", ["missing_evidence", "unknown_status", "null_status", "wrong_period", "missing_semantics"])
def test_statistics_with_incomplete_or_unqualified_annotations_are_withheld(mutation):
    frame = evidence.annotate_fiu_statistics(pd.DataFrame([fiu._reporting_statistics_rows()[0].__dict__]))
    if mutation == "missing_evidence":
        frame = frame.drop(columns="reference_verification_status")
    elif mutation == "unknown_status":
        frame["reference_verification_status"] = "created"
    elif mutation == "null_status":
        frame["reference_verification_status"] = pd.Series([pd.NA],dtype="string")
    elif mutation == "wrong_period":
        frame["reporting_period"] = "2024-Q1"
    else:
        frame = frame.drop(columns="semantic_review_status")
    selected = evidence.select_fiu_public_context(frame, "statistics")
    assert selected.frame.empty and selected.withheld_rows == 1


def test_annual_and_mixed_support_are_withheld_but_quarterly_context_is_kept():
    frame = evidence.annotate_fiu_typologies(pd.DataFrame([r.__dict__ for r in fiu._typology_support_rows()]))
    selected = evidence.select_fiu_public_context(frame, "typologies")
    assert selected.frame.typology_support_id.tolist() == ["FIU-TYP-006"]
    assert selected.withheld_rows == 6
    assert len(frame) == 7


def test_missing_and_empty_optional_tables_and_invalid_family():
    assert evidence.select_fiu_public_context(None,"referrals").frame is None
    assert evidence.select_fiu_public_context(pd.DataFrame(),"referrals").withheld_rows == 0
    with pytest.raises(ValueError):
        evidence.select_fiu_public_context(pd.DataFrame(),"unknown")


def test_report_passes_only_eligible_context_and_real_period_and_notes_columns(monkeypatch):
    sources = evidence.annotate_fiu_sources(pd.DataFrame([r.__dict__ for r in fiu._source_register_rows()]))
    stats = evidence.annotate_fiu_statistics(pd.DataFrame([r.__dict__ for r in fiu._reporting_statistics_rows()]))
    referrals = evidence.annotate_fiu_referrals(pd.DataFrame([r.__dict__ for r in fiu._case_referral_rows()]))
    types = evidence.annotate_fiu_typologies(pd.DataFrame([r.__dict__ for r in fiu._typology_support_rows()]))
    tables = {"waris_fiu_official_source_register.csv":sources, "waris_fiu_reporting_statistics_context.csv":stats,
              "waris_fiu_case_referral_context.csv":referrals, "waris_fiu_typology_support_register.csv":types}
    monkeypatch.setattr(report_generator,"_load_table",lambda name:tables.get(name))
    calls=[]
    def capture_table(frame, columns, **kwargs):
        calls.append((frame.copy(), columns))
        return report_generator.Spacer(1,1)
    monkeypatch.setattr(report_generator,"_table_from_df",capture_table)
    styles=getSampleStyleSheet();styles.add(report_generator.ParagraphStyle(name="Small",fontSize=8))
    story=[];report_generator._build_fiu_official_context_section(story,styles)
    stats_frame,stats_columns=next((f,c) for f,c in calls if "metric_name" in c)
    types_frame,_=next((f,c) for f,c in calls if "typology_support_id" in c)
    _,source_columns=next((f,c) for f,c in calls if "source_id" in c)
    assert len(stats_frame)==12 and "notes" in stats_columns and "interpretation" not in stats_columns
    assert "reporting_period" in source_columns and "source_period" not in source_columns
    assert types_frame.typology_support_id.tolist()==["FIU-TYP-006"]
    assert any("Withheld rows: statistics=1, referrals=0, typologies=6" in getattr(x,"text","") for x in story)
