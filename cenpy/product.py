
from configparser import ConfigParser
import pkg_resources

import geopandas as gpd
import pandas as pd

from cenpy.census import CensusDataset
from cenpy.tiger import EsriMapServer
from cenpy.utils import RestApiBase, lazy_property


CONFIG = pkg_resources.resource_filename(__name__, 'conf/geographies.ini')


class ProductBase(RestApiBase):

    def __init__(self, year, config=CONFIG, session=None):
        self.year = year

        self.config = ConfigParser()
        self.config.read(config)

        super(ProductBase, self).__init__(session=session)

    @lazy_property
    def _legislative_year(self):
        return self.year - (self.year % 2)

    @lazy_property
    def _census_year(self):
        return f'{self.year - (self.year % 10)} Census'

    @lazy_property
    def _congressional_district(self):
        return 'NotImplementedYet'

    @lazy_property
    def _variable_lookup(self):
        return dict(self.config.items('variables'))

    @lazy_property
    def _layer_lookup(self):
        return dict(self.config.items('layers'))

    def query(
        self,
        get: dict,
        for_dict: dict,
        in_dict: dict = None,
        key: str = None,
        **kwargs,
    ) -> pd.DataFrame:

        if not isinstance(get, list):
            get = [get]

        if len(for_dict) != 1:
            raise Exception

        # ensure GEO_ID is included, for merging purposes
        if 'GEO_ID' not in get:
            get.append('GEO_ID')

        # get census data
        df = self._census.query(get, for_dict, in_dict, key)

        # rename GEO_ID to GEOID, split on 'US')
        df['GEOID'] = df['GEO_ID'].str.split('US').str[1]
        df.drop('GEO_ID', axis=1, inplace=True)

        # filter geographies for reordering columns
        for_geography, for_value = list(for_dict.items())[0]
        geographies = [
            i for i in df.columns if i in list(self._census.geographies.name)
        ]

        # if geography not in inString, assume wildcard
        # if geography has wildcard, do not include in sql
        if in_dict is None:
            in_dict = {}

        sql_dict = {
            self._variable_lookup[k]: v for k, v in {**in_dict, **for_dict}.items() if v != '*'
        }

        # construct sql where
        sql_where = ' AND '.join(
            f"{k} IN ('{v}')" for k, v in sql_dict.items()
        )

        if sql_where == '':
            sql_where = '1=1'

        # only pull GEOID for merge
        outFields = kwargs.pop('outFields', '')

        if isinstance(outFields, list):
            outFields = ','.join(outFields)

        # add NAME for ease, GEOID for merging
        outFields += 'NAME,GEOID'

        # get layer name from .ini file
        # format if {} exists in string
        # if ',' present, query multiple layers (will have side effect on resultRecordCount)
        layername_s = self._layer_lookup[for_geography].format(
            census_year=self._census_year,
            legislative_year=self._legislative_year,
            congressional_district=self._congressional_district,
        )

        layername_s = [layer.strip() for layer in layername_s.split(',')]

        returnGeometry = kwargs.pop('returnGeometry', True)
        geometryPrecision = kwargs.pop('geometryPrecision', 2)

        # census data (american indian area/alaska native area/hawaiian home
        # land) does not have letter at end of GEOID, but tigerweb does; set
        # flag to strip from tigerweb later
        aiannh_strip_letter = False
        if for_geography in ['american indian area/alaska native area/hawaiian home land']:
            aiannh_strip_letter = True

        sdf = pd.DataFrame()
        for name in layername_s:

            # get tigerweb data
            result = self._tiger.layers[name].query(
                where=sql_where,
                outFields=outFields,
                returnGeometry=returnGeometry,
                geometryPrecision=geometryPrecision,
                **kwargs,
            )

            if result.shape == (0, 0):
                continue

            # drop R/T from end of GEOID to match up with census
            if aiannh_strip_letter:
                result['GEOID'] = result['GEOID'].str.replace('R', '')
                result['GEOID'] = result['GEOID'].str.replace('T', '')

            if sdf.shape > (0, 0):
                sdf = sdf.append(result, ignore_index=True)

            else:
                sdf = result

        # merge dataframes
        combined = pd.merge(df, sdf, on=['GEOID'])

        # drop any duplicate GEOID (targetted to AIANNH)
        combined = combined.loc[combined['GEOID'].drop_duplicates().index].reset_index(drop=True)

        # reorder columns
        outFields = outFields.split(',')
        combined = combined[
            geographies +
            outFields +
            [i for i in combined.columns if i not in geographies + outFields]
        ]

        if 'geometry' in combined.columns:
            combined = gpd.GeoDataFrame(combined)

        return combined


class ACS(ProductBase):

    def __init__(self, year, session=None):
        super(ACS, self).__init__(year, session=session)
        self._census = CensusDataset(
            f'https://api.census.gov/data/{self.year}/acs/acs5',
            session=self._session,
        )
        self._tiger = EsriMapServer(
            f'https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/tigerWMS_ACS{self.year}/MapServer',
            session=self._session,
        )


class Decennial(ProductBase):

    def __init__(self, year, session=None):
        super(Decennial, self).__init__(year, session=session)
        self._census = CensusDataset(
            f'https://api.census.gov/data/{self.year}/dec/sf1',
            session=self._session,
        )
        self._tiger = EsriMapServer(
            f'https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/tigerWMS_Census{self.year}/MapServer',
            session=self._session,
        )

    @lazy_property
    def legislative_year(self):
        return 'NotImpementedError'

    @lazy_property
    def census_year(self):
        return ''

    @lazy_property
    def congressional_district(self):
        return 'NotImpementedError'


if __name__ == '__main__':

    acs = ACS(2019)
    data = acs.query('B01001_001E', {'tract': '*'}, {'state': '06', 'county': '071'}, key='a4b2eab7c7050050923fffa485fb81e22be63e68')
    print(data.head())
