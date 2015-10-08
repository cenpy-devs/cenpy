from six import iteritems as diter
import requests as r
import pandas as pd
#all queries to a map server, mounted at
#tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/
#are mounted by adding <name>/<MapServer> if they're mapservers

#none of the types at that url?f=json are not Mapservers.

_baseurl = "http://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb"
_pcs = "https://developers.arcgis.com/javascript/jshelp/pcs.html"
_bcs = "https://developers.arcgis.com/javascript/jshelp/bcs.html"

def _jget(st):
    return r.get(st + '?f=json')

def available(verbose=False):
    """
    Query the TIGERweb geoAPI for available MapServices

    Parameters
    -----------
    verbose :   int
                int/bool describing verbosity level. Accepts levels -1, 0, 1, and
                greater.

    Returns
    -------
    list or dict of available MapServers through TIGERweb
    """
    q = _jget(_baseurl).json()
    for d in q['services']:
        d['name'] = d['name'].split('/')[-1]
    if verbose == -1:
        return [d['name'] for d in q['services']]
    if not verbose:
        return q['services']
    else:
        print('verbose may take a bit...')
        nexturls = ['/'.join([_baseurl, d['name'], d['type']]) for d in q['services']]
        for i,d in enumerate(q['services']):
            d['description'] = _jget(nexturls[i]).json()['description']
        if verbose == True:
            return q['services']
        else:
            return q

class ESRILayer(object):
    def __init__(self, baseurl, **kwargs):
        self.__dict__.update({'_'+k:v for k,v in diter(kwargs)})
        if hasattr(self, '_fields'):
            self.variables = pd.DataFrame(self._fields)
        self._baseurl = baseurl + '/' + str(self._id)

    def __repr__(self):
        try:
            return '(ESRILayer) ' + self._name
        except:
            return ''

class TigerConnection(object):
    """
    a tiger connection
    """
    def __init__(self, name = None):
        if name not in available(verbose=-1):
            raise KeyError('Dataset {n} not found. Please check cenpy.tiger.available()'.format(n=name))
        else:
            self._baseurl = '/'.join([_baseurl, name, 'MapServer'])
            resp = _jget(self._baseurl).json()
            self._key = name
            self.name = resp.pop('mapName', name)
            self.layers = self._get_layers()
            self.copyright = resp['copyrightText']
            self.projection = resp['spatialReference']['latestWKid']

    def _get_layers(self):
        resp = _jget(self._baseurl + '/layers').json()
        return {d['id']:ESRILayer(self._baseurl, **d) for d in resp['layers']}

