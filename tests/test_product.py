
import pandas as pd
import pytest

from cenpy import ACS, Decennial

@pytest.fixture(scope='module')
def ACSProductApi():
    api = ACS(2019)
    return api

@pytest.fixture(scope='module')
def DecennialProductApi():
    api = Decennial(2010)
    return api

shared_geography_params = [
    ({'region': '1'}, None),
    ({'division': '1'}, None),
    ({'state': '11'}, None),
    ({'county': '610'}, {'state': '51'}),
    ({'county subdivision': '25970'}, {'state': '39', 'county': '061'}),
    ({'subminor civil division': '21888'}, {'state': '72', 'county': '011', 'county subdivision': '02637'}),
    ({'tract': '990300'}, {'state': '06', 'county': '037'}),
    ({'block group': '0'}, {'state': '06', 'county': '037', 'tract': '990300'}),
    ({'place': '60290'}, {'state': '48'}),
    ({'consolidated city': '47500'}, {'state': '09'}),
    ({'alaska native regional corporation': '41640'}, {'state': '02'}),
    ({'american indian area/alaska native area/hawaiian home land': '6915'}, None),
    ({'tribal census tract': 'T00100'}, {'american indian area/alaska native area/hawaiian home land': '1955'}),
    ({'tribal block group': 'A'}, {'american indian area/alaska native area/hawaiian home land': '1955', 'tribal census tract': 'T00100'}),
    ({'metropolitan statistical area/micropolitan statistical area': '45940'}, None),
    ({'metropolitan division': '37964'}, {'metropolitan statistical area/micropolitan statistical area': '37980'}),
    ({'combined statistical area': '408'}, None),
    ({'metropolitan statistical area/micropolitan statistical area': '45940'}, {'combined statistical area': '408'}),
    ({'combined new england city and town area': '770'}, None),
    ({'new england city and town area': '72500'}, {'combined new england city and town area': '725'}),
    ({'new england city and town area': '76150'}, None),
    ({'necta division': '74204'}, {'new england city and town area': '71650'}),
    ({'urban area': '22987'}, None),
    ({'school district (elementary)': '32340'}, {'state': '06'}),
    ({'school district (secondary)': '17903'}, {'state': '17'}),
    ({'school district (unified)': '00780'}, {'state': '34'}),
]


# '#': working - shared
# '#!': not working - (or part)
# '#!!': not working  - needs further look
acs_geography_params = [
#    ({'region': '1'}, None),
#    ({'division': '1'}, None),
#    ({'state': '11'}, None),
#    ({'county': '610'}, {'state': '51'}),
#    ({'county subdivision': '21000'}, {'state': '39', 'county': '057'}),
#    ({'subminor civil division': '21888'}, {'state': '72', 'county': '011', 'county subdivision': '02637'}),
#!    ({'place/remainder (or part)': '02680'}, {'state': '72', 'county': '011', 'county subdivision': '02637'}),
#    ({'tract': '990300'}, {'state': '06', 'county': '037'}),
#    ({'block group': '0'}, {'state': '06', 'county': '037', 'tract': '990300'}),
#!    ({'county (or part)': '427'}, {'state': '48', 'place': '60290'}),
#    ({'place': '60290'}, {'state': '48'}),
#    ({'consolidated city': '47500'}, {'state': '09'}),
#!    ({'place (or part)': '88050'}, {'state': '09', 'consolidated city': '47500'}),
#    ({'alaska native regional corporation': '41640'}, {'state': '02'}),
#    ({'american indian area/alaska native area/hawaiian home land': '6915'}, None),
    ({'american indian tribal subdivision': '160'}, {'american indian area/alaska native area/hawaiian home land': '3680'}),
    ({'american indian area/alaska native area (reservation or statistical entity only)': 'R'}, None),
    ({'american indian area (off-reservation trust land only)/hawaiian home land': 'T'}, None),
#    ({'tribal census tract': 'T00100'}, {'american indian area/alaska native area/hawaiian home land': '1955'}),
#    ({'tribal block group': 'A'}, {'american indian area/alaska native area/hawaiian home land': '1955', 'tribal census tract': 'T00100'}),
#!    ({'state (or part)': '06'}, {'american indian area/alaska native area/hawaiian home land': '1955'}),
#!    ({'place (or part)': '99999'}, {'american indian area/alaska native area/hawaiian home land': '1955', 'state (or part)': '06'}),
#!    ({'county (or part)': '049'}, {'american indian area/alaska native area/hawaiian home land': '1955', 'state (or part)': '06'}),
#!    ({'american indian area/alaska native area/hawaiian home land (or part)': '1955'}, {'state': '06'}),
#!    ({'american indian area/alaska native area (reservation or statistical entity only) (or part)': 'R'}, {'state': '06'}),
#!    ({'american indian area (off-reservation trust land only)/hawaiian home land (or part)': 'T'}, {'state': '06'}),
#!    ({'state (or part)': '27'}, {'american indian area/alaska native area/hawaiian home land': '3680', 'american indian tribal subdivision': '160'}),
#!    ({'tribal census tract (or part)': 'T00100'}, {'american indian area/alaska native area/hawaiian home land': '1955', 'american indian area/alaska native area (reservation or statistical entity only)': 'R'}),
#!    ({'tribal census tract (or part)': 'T00100'}, {'american indian area/alaska native area/hawaiian home land': '3195', 'american indian area (off-reservation trust land only)/hawaiian home land': 'T'}),
#!    ({'tribal block group (or part)': 'A'}, {'american indian area/alaska native area/hawaiian home land': '1955', 'american indian area/alaska native area (reservation or statistical entity only)': 'R', 'tribal census tract (or part)': 'T00100'}),
#!    ({'tribal block group (or part)': 'A'}, {'american indian area/alaska native area/hawaiian home land': '3195', 'american indian area (off-reservation trust land only)/hawaiian home land': 'T', 'tribal census tract (or part)': 'T00100'}),
#    ({'metropolitan statistical area/micropolitan statistical area': '45940'}, None),
#!    ({'state (or part)': '25'}, {'metropolitan statistical area/micropolitan statistical area': '47240'}),
#!    ({'principal city (or part)': '71970'}, {'metropolitan statistical area/micropolitan statistical area': '47240', 'state (or part)': '25'}),
#!    ({'county': '007'}, {'metropolitan statistical area/micropolitan statistical area': '47240', 'state (or part)': '25'}),
#    ({'metropolitan division': '37964'}, {'metropolitan statistical area/micropolitan statistical area': '37980'}),
#!    ({'state (or part)': '42'}, {'metropolitan statistical area/micropolitan statistical area': '37980', 'metropolitan division': '37964'}),
#!    ({'county': '045'}, {'metropolitan statistical area/micropolitan statistical area': '37980', 'metropolitan division': '37964', 'state (or part)': '42'}),
#!    ({'metropolitan statistical area/micropolitan statistical area (or part)': '37980'}, {'state': '42'}),
#!    ({'principal city (or part)': '60000'}, {'state': '42', 'metropolitan statistical area/micropolitan statistical area (or part)': '37980'}),
#!    ({'county': '045'}, {'state': '42', 'metropolitan statistical area/micropolitan statistical area (or part)': '37980'}),
#!    ({'metropolitan division (or part)': '37964'}, {'state': '42', 'metropolitan statistical area/micropolitan statistical area (or part)': '37980'}),
#!    ({'county': '045'}, {'state': '42', 'metropolitan statistical area/micropolitan statistical area (or part)': '37980', 'metropolitan division (or part)': '37964'}),
#    ({'combined statistical area': '408'}, None),
#!    ({'state (or part)': '18'}, {'combined statistical area': '458'}),
#    ({'metropolitan statistical area/micropolitan statisti22cal area': '45940'}, {'combined statistical area': '408'}),
#!    ({'state (or part)': '18'}, {'combined statistical area': '408', 'metropolitan statistical area/micropolitan statistical area': '18220'}),
#    ({'combined new england city and town area': '770'}, None),
#!    ({'state (or part)': '50'}, {'combined new england city and town area': '770'}),
#    ({'new england city and town area': '76150'}, {'combined new england city and town area': '408'}),
#!    ({'state (or part)': '50'}, {'combined new england city and town area': '770', 'new england city and town area': '76150'}),
#!    ({'combined statistical area (or part)': '458'}, {'state': '18'}),
#!    ({'metropolitan statistical area/micropolitan statistical area (or part)': '18220'}, {'state': '18', 'combined statistical area (or part)': '458'}),
#!    ({'combined new england city and town area (or part)': '770'}, {'state': '50'}),
#!    ({'new england city and town area (or part)': '76150'}, {'state': '50', 'combined new england city and town area (or part)': '770'}),
#    ({'new england city and town area': '76150'}, None),
#!    ({'state (or part)': '50'}, {'new england city and town area': '76150'}),
#!    ({'principal city': '46225'}, {'new england city and town area': '76150', 'state (or part)': '25'}),
#!    ({'county (or part)': '003'}, {'new england city and town area': '76150', 'state (or part)': '50'}),
#!    ({'county subdivision': '69775'}, {'new england city and town area': '76150', 'state (or part)': '50', 'county (or part)': '003'}),
#    ({'necta division': '74204'}, {'new england city and town area': '71650'}),
#!    ({'state (or part)': '25'}, {'new england city and town area': '71650', 'necta division': '74854'}),
#!    ({'county (or part)': '009'}, {'new england city and town area': '71650', 'necta division': '74854', 'state (or part)': '25'}),
#!    ({'county subdivision': '43580'}, {'new england city and town area': '71650', 'necta division': '74854', 'state (or part)': '25', 'county (or part)': '009'}),
#!    ({'new england city and town area (or part)': '76150'}, {'state': '50'}),
#!    ({'principal city': '46225'}, {'state': '25', 'new england city and town area (or part)': '76150'}),
#!    ({'county (or part)': '003'}, {'state': '50', 'new england city and town area (or part)': '76150'}),
#!    ({'county subdivision': '69775'}, {'state': '50', 'new england city and town area (or part)': '76150', 'county (or part)': '003'}),
#!    ({'necta division (or part)': '74854'}, {'state': '25', 'new england city and town area (or part)': '71650'}),
#!    ({'county (or part)': '009'}, {'state': '25', 'new england city and town area (or part)': '71650', 'necta division (or part)': '74854'}),
#!    ({'county subdivision': '43580'}, {'state': '25', 'new england city and town area (or part)': '71650', 'necta division (or part)': '74854', 'county (or part)': '009'}),
#    ({'urban area': '22987'}, None),
#!    ({'state (or part)': '06'}, {'urban area': '22987'}),
#!    ({'county (or part)': '029'}, {'urban area': '22987', 'state (or part)': '06'}),
#    ({'congressional district': '13'}, {'state': '36'}),
#!    ({'county (or part)': '061'}, {'state': '36', 'congressional district': '13'}),
#!    ({'american indian area/alaska native area/hawaiian home land (or part)': '6915'}, {'state': '02', 'congressional district': '00'}),
    ({'state legislative district (upper chamber)': '016'}, {'state': '44'}),
#!    ({'county (or part)': '007'}, {'state': '44', 'state legislative district (upper chamber)': '016'}),
    ({'state legislative district (lower chamber)': '726'}, {'state': '33'}),
#!    ({'county (or part)': '015'}, {'state': '33', 'state legislative district (lower chamber)': '726'}),
    ({'public use microdata area': '03803'}, {'state': '36'}),
#!!    ({'zip code tabulation area': '82073'}, {'state': '*'}),
#    ({'school district (elementary)': '32340'}, {'state': '06'}),
#    ({'school district (secondary)': '17903'}, {'state': '17'}),
#    ({'school district (unified)': '00780'}, {'state': '34'}),
]


dec_geography_params = [
]


@pytest.mark.parametrize('for_dict, in_dict', shared_geography_params + acs_geography_params)
def test_all_acs_geographies(ACSProductApi, for_dict, in_dict):

    # autofail '(or part)' tests
    if any('(or part)' in k for k in for_dict):
        assert False

    data = ACSProductApi.query(
        'B01001_001E',
        for_dict,
        in_dict,
        key='a4b2eab7c7050050923fffa485fb81e22be63e68',
        returnGeometry=True,
        resultRecordCount=1,
    )
    assert isinstance(data, pd.DataFrame)
    assert data.shape > (0, 0)
    assert 'geometry' in data.columns


@pytest.mark.parametrize('for_dict, in_dict', shared_geography_params + dec_geography_params)
def test_all_dec_geographies(DecennialProductApi, for_dict, in_dict):

    # autofail '(or part)' tests
    if any('(or part)' in k for k in for_dict):
        assert False

    data = DecennialProductApi.query(
        'H001001',
        for_dict,
        in_dict,
        key='a4b2eab7c7050050923fffa485fb81e22be63e68',
        returnGeometry=True,
        resultRecordCount=1,
        geometryPrecision=0,
        orderByFields='AREALAND',
    )
    assert isinstance(data, pd.DataFrame)
    assert data.shape > (0, 0)
    assert 'geometry' in data.columns


def test_chunked_query(ACSProductApi):
    data = ACSProductApi.query(
        'B01001_001E',
        {'county': '*'},
        {'state': ['02', '48', '06', '30', '35', '04', '32', '08']},
        key='a4b2eab7c7050050923fffa485fb81e22be63e68',
    )
    assert isinstance(data, pd.DataFrame)
    assert data.shape > (0, 0)
