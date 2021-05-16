import pandas as pd
import pytest

from cenpy import tiger
from cenpy.tiger import EsriMapServiceLayer


@pytest.fixture(scope="module")
def TigerApi():
    api = EsriMapServiceLayer(
        "https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/tigerWMS_ACS2019/MapServer/86"
    )
    return api


def test_returnGeometry_false(TigerApi):
    data = TigerApi.query(where="AREALAND>0", resultRecordCount=1, returnGeometry=False)
    assert isinstance(data, pd.DataFrame)
    assert "geometry" not in data.columns


def test_fail_on_chunked_query(TigerApi):
    with pytest.raises(Exception):
        tiger.CHUNKED_QUERY_NUMBER_OF_CHUNKS = 1
        data = TigerApi.query(
            where="1=1", geometryPrecision=12, outFields="*", returnGeometry=True
        )
    tiger.CHUNKED_QUERY_NUMBER_OF_CHUNKS = 2
