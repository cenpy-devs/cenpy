from six import iteritems as diter
import requests as r
import pandas as pd
from geopandas import GeoDataFrame
import copy

from . import geoparser as gpsr

# all queries to a map server, mounted at
# tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/
# are mounted by adding <name>/<MapServer> if they're mapservers

# none of the types at that url?f=json are not Mapservers.

_baseurl = "http://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb"
_pcs = "https://developers.arcgis.com/javascript/jshelp/pcs.html"
_bcs = "https://developers.arcgis.com/javascript/jshelp/bcs.html"

_basequery = {'where': '',  # sql query component
              'text': '',  # raw text search
              'objectIds': '',  # only grab these objects
              'time': '',  # time instant/time extend to query
              'geometry': '',  # spatial filter to apply to query
              'geometryType': 'esriGeometryEnvelope',  # spatial support
              'inSR': '',  # spatial ref of input geometry
              'spatialRel': '',  # what to do in a DE9IM spatial query
              'relationParam': '',  # used if arbitrary spatialRel is applied
              'outFields': '*',  # fields to pass from the header out
              'returnGeometry': True,  # bool describing whether to pass geometry out
              'maxAllowableOffset': '',  # set a spatial offset
              'geometryPrecision': '',
              'outSR': '',  # spatial reference of returned geometry
              'returnIdsOnly': False,  # bool stating to only return ObjectIDs
              'returnCountOnly': False,  # not documented, probably for the sql query
              'orderByFields': '',  # again not documented, probably for the sql
              'groupByFieldsForStatistics': '',  # not documented, probably for sql
              'outStatistics': '',  # no clue
              'returnZ': False,  # whether to return z components of shp-z
              'returnM': False,  # whether to return m components of shp-m
              'gdbVersion': '',  # geodatabase version name
              'returnDistinctValues': ''}  # no clue


def _jget(st):
    return r.get(st + '?f=json')


def available(verbose=False):
    """
    Query the TIGERweb geoAPI for available MapServices

    Parameters
    -----------
    verbose :   int or bool
                indicator for the verbosity level. Accepts levels -1, 0, 1, and greater.

    Returns
    -------
    list or dict of available MapServers through TIGERweb
    """
    q = _jget(_baseurl)
    q.raise_for_status()
    q = q.json()
    for d in q['services']:
        d['name'] = d['name'].split('/')[-1]
    if verbose == -1:
        return [d['name'] for d in q['services']]
    if not verbose:
        return q['services']
    else:
        print('verbose may take a bit...')
        nexturls = ['/'.join([_baseurl, d['name'], d['type']])
                    for d in q['services']]
        for i, d in enumerate(q['services']):
            resp = _jget(nexturls[i])
            resp.raise_for_status()
            d['description'] = resp.json()['description']
        if verbose == True:
            return q['services']
        else:
            return q


class ESRILayer(object):
    """The fundamental building block to access a single Geography/Layer in an ESRI MapService"""
    def __init__(self, baseurl, **kwargs):
        """
        Class representing the ESRI Layer in the TIGER API

        Parameters
        ----------
        baseurl :   str
                    the url for the Layer. 

        """
        self.__dict__.update({'_'+k: v for k, v in diter(kwargs)})
        if hasattr(self, '_fields'):
            self.variables = pd.DataFrame(self._fields)
        self._baseurl = baseurl + '/' + str(self._id)

    def __repr__(self):
        try:
            return '(ESRILayer) ' + self._name
        except:
            return ''

    def query(self, raw=False, strict=False, **kwargs):
        """
        A query function to extract data out of MapServer layers. I've exposed
        every option here 

        Parameters
        ---------- 
        where: str, required
                    sql query string. 
        out_fields: list or str
                    fields to pass from the header out (default: '*')
        return_geometry: bool
                    bool describing whether to return geometry or just the
                    dataframe. (default: True)
        geometry_precision: str
                    a number of significant digits to which the output of the
                    query should be truncated (default: None)
        out_sr: int or str
                    ESRI WKID spatial reference into which to reproject 
                    the geodata (default: None)
        return_ids_only: bool
                    bool stating to only return ObjectIDs. (default: False)
        return_z: bool
                     whether to return z components of shp-z, (default: False)
        return_m: bool
                     whether to return m components of shp-m, (default: False)
        strict  :   bool
                    whether to throw an error if invalid polygons are provided from the API (True)
                    or just warn that at least one polygon is invalid (default: False)
        raw : bool
              whether to provide the raw geometries from the API  (default: False)
        
        Returns
        ------- 
        Dataframe or GeoDataFrame containing entries from the geodatabase

        Notes
        -----
        Most of the time, this should be used leaning on the SQL "where"
        argument: 

        cxn.query(where='GEOID LIKE "06*"')

        In most cases, you'll be querying against layers, not MapServices
        overall. 
        """
    # parse args
        kwargs = {''.join(k.split('_')): v for k, v in diter(kwargs)}

    # construct query string
        self._basequery = copy.deepcopy(_basequery)
        for k, v in diter(kwargs):
            try:
                self._basequery[k] = v
            except KeyError:
                raise KeyError("Option '{k}' not recognized, check parameters")
        qstring = '&'.join(['{}={}'.format(k, v)
                            for k, v in diter(self._basequery)])
        self._last_query = self._baseurl + '/query?' + qstring
    # run query
        resp = r.get(self._last_query + '&f=json')
        resp.raise_for_status()
        datadict = resp.json()
        if raw:
            return datadict
        if kwargs.get('returnGeometry', 'true') is 'false':
            return pd.DataFrame.from_records([x['attributes'] for x in datadict['features']])
    # convert to output format
        try:
            features = datadict['features']
        except KeyError:
            code, msg = datadict['error']['code'], datadict['error']['message']
            details = datadict['error']['details']
            if details is []:
                details = 'Mapserver provided no detailed error'
            raise KeyError((r'Response from API is malformed. You may have '
                            r'submitted too many queries, formatted the request incorrectly, '
                            r'or experienced significant network connectivity issues.'
                            r' Check to make sure that your inputs, like placenames, are spelled'
                            r' correctly, and that your geographies match the level at which you'
                            r' intend to query. The original error from the Census is:\n'
                            r'(API ERROR {}:{}({}))'.format(code, msg, details)))
        todf = []
        for i, feature in enumerate(features):
            locfeat = gpsr.__dict__[datadict['geometryType']](feature)
            todf.append(locfeat['properties'])
            todf[i].update({'geometry': locfeat['geometry']})
        df = pd.DataFrame(todf)
        outdf = gpsr.convert_geometries(df, strict=strict)
        outdf = GeoDataFrame(outdf)
        crs = datadict.pop('spatialReference', None)
        if crs is not None:
            crs = crs.get('latestWkid', crs.get('wkid'))
            crs = dict(init='epsg:{}'.format(crs))
        outdf.crs = crs
        return outdf


class TigerConnection(object):
    """The fundamental building block for US Census Bureau's Geographic, an ESRI MapService"""

    def __init__(self, name=None):
        """
        Parameters
        ----------
        name    :   str
                    string describing the API to connect to

        """
        if name not in available(verbose=-1):
            raise KeyError(
                'Dataset {n} not found. Please check cenpy.tiger.available()'.format(n=name))
        else:
            self._baseurl = '/'.join([_baseurl, name, 'MapServer'])
            resp = _jget(self._baseurl)
            resp.raise_for_status()
            resp = resp.json()
            self._key = name
            self.title = resp.pop('mapName', name)
            self.layers = self._get_layers()
            self.copyright = resp['copyrightText']
            self.projection = resp['spatialReference']['latestWkid']

    def _get_layers(self):
        resp = _jget(self._baseurl + '/layers')
        resp.raise_for_status()
        resp = resp.json()
        return [ESRILayer(self._baseurl, **d) for d in resp['layers']]

    def query(self, **kwargs):
        """
        method to query the ESRI API. Passes down to an appropriately-chosen layer. 
        """
        layer_result = kwargs.pop('layer', None)
        if isinstance(layer_result, str):
            from .products import _fuzzy_match
            layer_result = _fuzzy_match(layer_result, 
                                        [f.__repr__() for f in self.layers]).index
        if layer_result is None:
            raise Exception('No layer selected.')
        return self.layers[layer_result].query(**kwargs)
