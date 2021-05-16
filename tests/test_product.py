import pandas as pd
import pytest

from cenpy import ACS, Decennial
from cenpy import tiger


@pytest.fixture(scope="module")
def ACSProductApi():
    api = ACS(2019)
    return api


@pytest.fixture(scope="module")
def ACS2018ProductApi():
    api = ACS(2018)
    return api


@pytest.fixture(scope="module")
def DecennialProductApi():
    api = Decennial(2010)
    return api


shared_geography_params = [
    ({"region": "1"}, {}),
    ({"division": "1"}, {}),
    ({"state": "11"}, {}),
    ({"county": "610"}, {"state": "51"}),
    ({"county subdivision": "25970"}, {"state": "39", "county": "061"}),
    (
        {"subminor civil division": "21888"},
        {"state": "72", "county": "011", "county subdivision": "02637"},
    ),
    ({"tract": "990300"}, {"state": "06", "county": "037"}),
    ({"block group": "0"}, {"state": "06", "county": "037", "tract": "990300"}),
    ({"place": "60290"}, {"state": "48"}),
    ({"consolidated city": "47500"}, {"state": "09"}),
    ({"alaska native regional corporation": "41640"}, {"state": "02"}),
    ({"american indian area/alaska native area/hawaiian home land": "6915"}, {}),
    (
        {"tribal census tract": "T00100"},
        {"american indian area/alaska native area/hawaiian home land": "1955"},
    ),
    (
        {"tribal block group": "A"},
        {
            "american indian area/alaska native area/hawaiian home land": "1955",
            "tribal census tract": "T00100",
        },
    ),
    ({"metropolitan statistical area/micropolitan statistical area": "45940"}, {}),
    (
        {"metropolitan division": "37964"},
        {"metropolitan statistical area/micropolitan statistical area": "37980"},
    ),
    ({"combined statistical area": "408"}, {}),
    (
        {"metropolitan statistical area/micropolitan statistical area": "45940"},
        {"combined statistical area": "408"},
    ),
    ({"combined new england city and town area": "770"}, {}),
    (
        {"new england city and town area": "72500"},
        {"combined new england city and town area": "725"},
    ),
    ({"new england city and town area": "76150"}, {}),
    ({"necta division": "74204"}, {"new england city and town area": "71650"}),
    ({"urban area": "22987"}, {}),
    ({"school district (elementary)": "32340"}, {"state": "06"}),
    ({"school district (secondary)": "17903"}, {"state": "17"}),
    ({"school district (unified)": "00780"}, {"state": "34"}),
]

acs_geography_params = [
    (
        {"american indian tribal subdivision": "160"},
        {"american indian area/alaska native area/hawaiian home land": "3680"},
    ),
    (
        {
            "american indian area/alaska native area (reservation or statistical entity only)": "R"
        },
        {},
    ),
    (
        {
            "american indian area (off-reservation trust land only)/hawaiian home land": "T"
        },
        {},
    ),
    (
        {"metropolitan statistical area/micropolitan statistical area": "45940"},
        {"combined statistical area": "408"},
    ),
    ({"combined new england city and town area": "770"}, {}),
    ({"congressional district": "13"}, {"state": "36"}),
    ({"state legislative district (upper chamber)": "016"}, {"state": "44"}),
    ({"state legislative district (lower chamber)": "726"}, {"state": "33"}),
    ({"public use microdata area": "03803"}, {"state": "36"}),
    ##    ({'zip code tabulation area': '82073'}, {'state': '56'}),
    ({"school district (elementary)": "32340"}, {"state": "06"}),
    ({"school district (secondary)": "17903"}, {"state": "17"}),
    ({"school district (unified)": "00780"}, {"state": "34"}),
]

dec_geography_params = [
    ({"block": "2016"}, {"state": "29", "county": "510", "tract": "107300"}),
    (
        {"tribal subdivision/remainder": "160"},
        {"american indian area/alaska native area/hawaiian home land": "3680"},
    ),
    (
        {
            "american indian area/alaska native area (reservation or statistical entity only)": "R"
        },
        {"american indian area/alaska native area/hawaiian home land": "6915"},
    ),
    (
        {
            "american indian area (off-reservation trust land only)/hawaiian home land": "T"
        },
        {"american indian area/alaska native area/hawaiian home land": "5196"},
    ),
    ##    ({'principal city': '*'}, {'new england city and town area': '76150'}),
    ({"congressional district": "13"}, {"state": "36"}),
    ##    ({'alaska native regional corporation': '*'}, {'state': '02', 'congressional district': '00'}),
    ({"state legislative district (upper chamber)": "016"}, {"state": "06"}),
    ({"state legislative district (lower chamber)": "056"}, {"state": "44"}),
    ({"zip code tabulation area": "82073"}, {}),
]


@pytest.mark.parametrize(
    "for_dict, in_dict", shared_geography_params + acs_geography_params
)
def test_acs_geographies(ACSProductApi, for_dict, in_dict):

    # autofail '(or part)' tests
    if any("(or part)" in k for k in for_dict):
        assert False

    data = ACSProductApi.query(
        ["B01001_001E"],
        for_dict,
        in_dict,
        key="a4b2eab7c7050050923fffa485fb81e22be63e68",
        returnGeometry=True,
        resultRecordCount=1,
    )
    assert isinstance(data, pd.DataFrame)
    assert data.shape > (0, 0)
    assert "geometry" in data.columns


@pytest.mark.parametrize(
    "for_dict, in_dict", shared_geography_params + dec_geography_params
)
def test_dec_geographies(DecennialProductApi, for_dict, in_dict):

    # autofail '(or part)' tests
    if any("(or part)" in k for k in for_dict):
        assert False

    data = DecennialProductApi.query(
        ["H001001"],
        for_dict,
        in_dict,
        key="a4b2eab7c7050050923fffa485fb81e22be63e68",
        returnGeometry=True,
        resultRecordCount=1,
        geometryPrecision=0,
        orderByFields="AREALAND",
    )
    assert isinstance(data, pd.DataFrame)
    assert data.shape > (0, 0)
    assert "geometry" in data.columns


def test_chunked_query(ACSProductApi):
    tiger.CHUNKED_QUERY_NUMBER_OF_CHUNKS = 2
    data = ACSProductApi.query(
        ["B01001_001E"],
        {"county": "*"},
        {"state": ["02", "48", "06", "30", "35", "04", "32", "08", "41"]},
        key="a4b2eab7c7050050923fffa485fb81e22be63e68",
    )
    assert isinstance(data, pd.DataFrame)
    assert data.shape > (0, 0)


def test_even_year_acs_congressional_district(ACS2018ProductApi):
    assert ACS2018ProductApi._congressional_district == "116th"


def test_not_implemented_error_geography(ACSProductApi):
    with pytest.raises(NotImplementedError):
        ACSProductApi.query(
            ["B01001_001E"],
            {"county (or part)": "427"},
            {"state": "48", "place": "60290"},
            key="a4b2eab7c7050050923fffa485fb81e22be63e68",
        )


def test_invalid_for_dict(ACSProductApi):
    with pytest.raises(Exception):
        ACSProductApi.query(
            ["B01001_001E"],
            {"county": "*", "state": "06"},
            {},
            key="a4b2eab7c7050050923fffa485fb81e22be63e68",
        )
