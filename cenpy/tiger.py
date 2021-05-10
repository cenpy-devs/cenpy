
import geopandas as gpd
import pandas as pd

from cenpy.geoparser import esri_geometry_polygon_to_shapely
from cenpy.utils import RestApiBase, lazy_property, chunks

QUERY_PARAMS = [
    'text',
    'geometry',
    'geometryType',
    'inSR',
    'spatialRel',
    'relationParam',
    'where',
    'objectIds',
    'time',
    'distance',
    'units',
    'outFields',
    'returnGeometry',
    'maxAllowableOffset',
    'geometryPrecision',
    'outSR',
    'returnIdsOnly',
    'returnCountOnly',
    'returnExtentOnly',
    'orderByFields',
    'outStatistics',
    'groupByFieldsForStatistics',
    'returnZ',
    'returnM',
    'gdbVersion',
    'returnDistinctValues',
    'returnTrueCurves',
    'resultOffset',
    'resultRecordCount',
    'datumTransformation',
    'rangeValues',
    'quantizationParameters',
    'parameterValues',
    'historicMoment',
    'f',
]

QUERY_DEFAULTS = {
    'where': '1=1',
    'geometryPrecision': 2,
    'geometryType': 'esriGeometryEnvelope',
    'spatialRel': 'esriSpatialRelIntersects',
    'units': 'esriSRUnit_Foot',
    'outFields': '*',
    'returnGeometry': False,
    'returnTrueCurves': False,
    'returnIdsOnly': False,
    'returnCountOnly': False,
    'returnZ': False,
    'returnM': False,
    'returnDistinctValues': False,
    'featureEncoding': 'esriDefault',
    'f': 'json',
}


class EsriMapServer(RestApiBase):

    def __init__(self, url, session=None):
        self.url = url
        super(EsriMapServer, self).__init__(session=session)

    @lazy_property
    def layers(self):
        response = self._get(f'{self.url}', params={'f': 'json'})
        response.raise_for_status()
        return {
            layer['name']: EsriMapServiceLayer(f'{self.url}/{layer["id"]}')
            for layer in response.json()['layers']
            if 'Labels' not in layer['name']
        }


class EsriMapServiceLayer(RestApiBase):

    def __init__(self, url, session=None):
        self.url = url
        super(EsriMapServiceLayer, self).__init__(session=session)

    def query(self, **kwargs):

        params = {}
        params.update(QUERY_DEFAULTS)
        params.update({k: v for k, v in kwargs.items() if k in QUERY_PARAMS})

        # overwrite return type to json (just in case)
        params['f'] = 'json'

#        from urllib.parse import urlencode; print(f'{self.url}/query?{urlencode(params)}')

        response = self._get(f'{self.url}/query', params=params)
        response.raise_for_status()

        data = response.json()

        # check to see if geometryType is present, if it is expect geometry
        if 'geometryType' in data:

            # if no features, return empty dataframe
            if len(data['features']) == 0:
                return gpd.GeoDataFrame()

#            geometryType = data['geometryType']
            spatialReference = data['spatialReference']

            spatial_data = []
            for row in data['features']:
                row['attributes']['geometry'] = row['geometry']
                spatial_data.append(row['attributes'])

            df = pd.DataFrame(spatial_data)

            # convert geometries to shapely
            df['geometry'] = df['geometry'].apply(esri_geometry_polygon_to_shapely)

            df = gpd.GeoDataFrame(df, geometry='geometry')
            df.set_crs(epsg=spatialReference['latestWkid'], inplace=True)

        else:
            df = pd.DataFrame([i['attributes'] for i in data['features']])

        return df
