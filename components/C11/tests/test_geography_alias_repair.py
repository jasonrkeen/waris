from src.live_data import standardize_oblast
from src.config import ACQUISITION_POLICY_VERSION


def test_observed_spelling_alias_and_address_context_map_to_canonical_region():
    for text in ['Zaporizhia','ZAPORIZHIA','Zaporizhia Oblast','Zaporizhzhia','Zaporizka']:
        assert standardize_oblast(text)=='Zaporizhzhia'
    assert ACQUISITION_POLICY_VERSION=='nbu-query-repair-1+oblast-alias-repair-1'


def test_repair_does_not_expand_scope_or_invent_unknown_geographies():
    for text in ['Crimea','not_a_geography',None]:
        assert standardize_oblast(text) is None
