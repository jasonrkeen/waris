import pandas as pd

from src import config, data_collection, wartime_aml_typology_register as literature


def configure(tmp_path, monkeypatch):
    monkeypatch.setattr(literature, 'TABLE_DIR', tmp_path)
    for name in ['TYPOLOGY_REGISTER_TABLE','TYPOLOGY_LAYER_MAP_TABLE','TYPOLOGY_SUMMARY_TABLE']:
        monkeypatch.setattr(literature, name, tmp_path/(name+'.csv'))


def test_public_exports_keep_general_literature_and_withhold_unverified_sfms_examples(tmp_path, monkeypatch):
    configure(tmp_path, monkeypatch)
    artifacts=literature.build_wartime_aml_typology_artifacts()
    register=artifacts['typology_register'];mapping=artifacts['typology_layer_map']
    assert register.typology_id.tolist()==list(config.WARTIME_PUBLIC_TYPOLOGY_IDS)
    assert len(mapping)==18
    assert len(literature._typologies())==10  # Annotated audit definitions are retained.
    assert register.source_license.eq('CC BY 4.0').all()
    assert 'recruitment' not in register.to_csv(index=False).lower()
    assert not register.used_in_waris_scoring.any() and not mapping.used_in_monte_carlo.any()


def test_direct_map_and_summary_calls_cannot_reintroduce_withheld_or_unknown_rows(tmp_path, monkeypatch):
    configure(tmp_path, monkeypatch)
    raw=pd.DataFrame([r.__dict__ for r in literature._typologies()])
    raw=pd.concat([raw,pd.DataFrame([{'typology_id':'unknown','typology_family':'unverified_family'}])],ignore_index=True)
    mapping=literature.build_wartime_aml_typology_layer_map(raw)
    assert set(mapping.typology_id)==set(config.WARTIME_PUBLIC_TYPOLOGY_IDS)
    summary=literature.build_wartime_aml_typology_summary(raw,mapping)
    assert summary.loc[summary.summary_area.eq('Typology register'),'value'].iloc[0]==6
    for text in ['occupation_related_finance','sector_payment_typologies','small_business_and_intermediary_accounts','intermediary_and_cash_typologies','unverified_family']:
        assert text not in summary.to_csv(index=False)


def test_public_crosswalk_uses_the_same_reduced_scope(tmp_path, monkeypatch):
    monkeypatch.setattr(data_collection,'RAW_DIR',tmp_path/'raw')
    monkeypatch.setattr(data_collection,'TABLE_DIR',tmp_path/'tables')
    crosswalk=data_collection.build_wartime_aml_typology_layer_alignment_crosswalk()
    assert len(crosswalk)==18
    assert set(crosswalk.reference_theme)==set(config.WARTIME_PUBLIC_ALIGNMENT_THEMES)
    assert crosswalk.production_score_change.eq('none').all()
