import pandas as pd

from Backend.processing import get_profile, get_raw_missing


def test_get_profile_uses_actual_missing_values():
    df = pd.DataFrame({
        "a": [1, None, 3],
        "b": ["x", "", None],
        "c": [10, 20, 30]
    })

    profile = get_profile(df)

    assert profile["total_missing"] == 3
    assert profile["column_details"][0]["missing"] == 1
    assert profile["column_details"][1]["missing"] == 2
    assert len(profile["preview"]) == 3
    assert profile["preview"][1]["a"] is None


def test_forest_raw_missing_ignores_headings_and_repaired_values(tmp_path):
    csv_content = """Bejaia Region Dataset
day,month,year,Temperature,RH,Ws,Rain,FFMC,DMC,DC,ISI,BUI,FWI,Classes
01,06,2012,29,57,18,0,65.7,3.4,7.6,1.3,3.4,0.5,not fire
Sidi-Bel Abbes Region Dataset
day,month,year,Temperature,RH,Ws,Rain,FFMC,DMC,DC,ISI,BUI,FWI,Classes
01,07,2012,29,,18,0,65.7,3.4,7.6,1.3,3.4,14.6 9
"""
    file_path = tmp_path / "forest.csv"
    file_path.write_text(csv_content, encoding="utf-8")

    total_missing, column_missing = get_raw_missing(file_path)

    assert total_missing == 1
    assert column_missing["RH"] == 1
    assert column_missing["FWI"] == 0


def test_profile_does_not_count_columns_absent_from_a_source_file():
    first_file = pd.DataFrame({"shared": [1, None], "first_only": [None, 4]})
    second_file = pd.DataFrame({"shared": [None], "second_only": [8]})
    combined = pd.concat([first_file, second_file], ignore_index=True)
    source_files = [
        {
            "name": "first.csv",
            "rows": len(first_file),
            "schema": list(first_file.columns),
        },
        {
            "name": "second.csv",
            "rows": len(second_file),
            "schema": list(second_file.columns),
        },
    ]

    profile = get_profile(combined, source_files=source_files)

    assert profile["total_missing"] == 3
    missing_by_column = {
        column["name"]: column["missing"]
        for column in profile["column_details"]
    }
    assert missing_by_column == {
        "shared": 2,
        "first_only": 1,
        "second_only": 0,
    }
    assert {row["Source File"] for row in profile["preview"]} == {
        "first.csv",
        "second.csv",
    }
    assert [group["name"] for group in profile["preview_groups"]] == [
        "first.csv",
        "second.csv",
    ]
    assert profile["preview_groups"][0]["columns"] == [
        "shared",
        "first_only",
    ]
    assert profile["preview_groups"][1]["columns"] == [
        "shared",
        "second_only",
    ]
