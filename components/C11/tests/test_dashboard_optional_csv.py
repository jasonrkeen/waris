import pandas as pd
import pytest

from src.utils import read_optional_dashboard_csv


@pytest.mark.parametrize("content", ["", "\n", "   \n"])
def test_columnless_optional_source_is_unavailable(tmp_path, content):
    path = tmp_path / "unavailable.csv"
    path.write_text(content, encoding="utf8")
    assert read_optional_dashboard_csv(path) is None
    assert read_optional_dashboard_csv(tmp_path / "missing.csv") is None


def test_valid_header_only_and_populated_data_keep_their_distinct_states(tmp_path):
    path = tmp_path / "source.csv"
    path.write_text("status,value\n", encoding="utf8")
    frame = read_optional_dashboard_csv(path)
    assert frame is not None and frame.empty and list(frame) == ["status", "value"]
    path.write_text("status,value\nchecked,42\n", encoding="utf8")
    assert read_optional_dashboard_csv(path).to_dict("records") == [{"status": "checked", "value": 42}]


def test_malformed_populated_data_is_not_silently_hidden(tmp_path):
    path = tmp_path / "malformed.csv"
    path.write_text('a,b\n1,2\n3,4,5\n', encoding="utf8")
    with pytest.raises(pd.errors.ParserError):
        read_optional_dashboard_csv(path)
