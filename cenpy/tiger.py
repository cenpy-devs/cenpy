import geopandas as gpd
import pandas as pd

from .geoparser import esri_geometry_polygon_to_shapely
from .utils import RestApiBase, lazy_property

QUERY_PARAMS = [
    "text",
    "geometry",
    "geometryType",
    "inSR",
    "spatialRel",
    "relationParam",
    "where",
    "objectIds",
    "time",
    "distance",
    "units",
    "outFields",
    "returnGeometry",
    "maxAllowableOffset",
    "geometryPrecision",
    "outSR",
    "returnIdsOnly",
    "returnCountOnly",
    "returnExtentOnly",
    "orderByFields",
    "outStatistics",
    "groupByFieldsForStatistics",
    "returnZ",
    "returnM",
    "gdbVersion",
    "returnDistinctValues",
    "returnTrueCurves",
    "resultOffset",
    "resultRecordCount",
    "datumTransformation",
    "rangeValues",
    "quantizationParameters",
    "parameterValues",
    "historicMoment",
    #    'f',  # remove as possibility to ignore any attempts to overwrite
]

QUERY_DEFAULTS = {
    "where": "1=1",
    "geometryPrecision": 2,
    "geometryType": "esriGeometryEnvelope",
    "spatialRel": "esriSpatialRelIntersects",
    "units": "esriSRUnit_Foot",
    "outFields": "*",
    "returnGeometry": False,
    "returnTrueCurves": False,
    "returnIdsOnly": False,
    "returnCountOnly": False,
    "returnZ": False,
    "returnM": False,
    "returnDistinctValues": False,
    "featureEncoding": "esriDefault",
    "f": "json",
}


CHUNKED_QUERY_NUMBER_OF_CHUNKS = 2


class EsriMapServer(RestApiBase):
    def __init__(self, url, session=None):
        self.url = url
        super(EsriMapServer, self).__init__(session=session)

    @lazy_property
    def layers(self):
        response = self._get(f"{self.url}", params={"f": "json"})
        response.raise_for_status()
        return {
            layer["name"]: EsriMapServiceLayer(f'{self.url}/{layer["id"]}')
            for layer in response.json()["layers"]
            if "Labels" not in layer["name"]
        }


class EsriMapServiceLayer(RestApiBase):
    def __init__(self, url, session=None):
        self.url = url
        super(EsriMapServiceLayer, self).__init__(session=session)

    def chunked_query(self, **kwargs):

        # returnCountOnly=True
        count_params = {}
        count_params.update(kwargs)
        count_params["returnCountOnly"] = True

        count_response = self._get(f"{self.url}/query", params=count_params)
        count_response.raise_for_status()
        count_data = count_response.json()
        count = count_data["count"]

        # divide count by #, use resultOffset and resultRecordCount to get in chunks
        offset = 0
        chunk_size = round(count / CHUNKED_QUERY_NUMBER_OF_CHUNKS + 0.5)

        result = {}
        for chunk in range(1, count, chunk_size):

            chunk_params = {}
            chunk_params.update(kwargs)
            chunk_params["resultOffset"] = offset
            chunk_params["resultRecordCount"] = (
                chunk_size if (offset + chunk_size) < count else count - offset
            )

            chunk_response = self._get(f"{self.url}/query", params=chunk_params)
            chunk_response.raise_for_status()
            chunk_data = chunk_response.json()

            if "error" in chunk_data:
                raise Exception

            if result == {}:
                result["features"] = result.get("features", []).append(
                    chunk_data["features"]
                )

            else:
                result.update(chunk_data)

            offset += chunk_size

        return result

    def query(self, **kwargs):

        params = {}
        params.update(QUERY_DEFAULTS)
        params.update({k: v for k, v in kwargs.items() if k in QUERY_PARAMS})

        #        from urllib.parse import urlencode; print(f'{self.url}/query?{urlencode(params)}')

        response = self._get(f"{self.url}/query", params=params)
        response.raise_for_status()

        data = response.json()

        # handle large transactions
        if "error" in data:
            if data["error"]["code"] == 500:
                data = self.chunked_query(**params)

        # check to see if geometryType is present, if it is expect geometry
        if "geometryType" in data:

            # if no features, return empty dataframe
            if len(data["features"]) == 0:
                return gpd.GeoDataFrame()

            #            geometryType = data['geometryType']
            spatialReference = data["spatialReference"]

            spatial_data = []
            for row in data["features"]:
                row["attributes"]["geometry"] = row["geometry"]
                spatial_data.append(row["attributes"])

            df = pd.DataFrame(spatial_data)

            # convert geometries to shapely
            df["geometry"] = df["geometry"].apply(esri_geometry_polygon_to_shapely)

            df = gpd.GeoDataFrame(df, geometry="geometry")
            df.set_crs(epsg=spatialReference["latestWkid"], inplace=True)

        else:
            df = pd.DataFrame([i["attributes"] for i in data["features"]])

        return df
