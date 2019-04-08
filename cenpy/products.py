from .remote import APIConnection
from .explorer import fips_table as _ft
from shapely import geometry
from fuzzywuzzy import fuzz
from warnings import warn
import geopandas
import pandas
import numpy
_places = _ft('place')
_places['TARGETFP'] = _places.PLACEFP.apply(lambda x: str(x).rjust(5, '0'))
_places['TARGETNAME'] = _places.PLACENAME
_places['STATEFP'] = _places.STATEFP.apply(lambda x: str(x).rjust(2, '0'))
_places.drop(['PLACEFP', 'FUNCSTAT', 'COUNTY', 'PLACENAME'], inplace=True, axis=1)

__all__ = ['Decennial2010', 'ACS']

class _Product(object):

    def __repr__(self):
        return self._api.__repr__()

    @property
    def variables(self):
        """All variables, including columns and search predictates,
         available from the API"""
        return self._api.variables.sort_index()
    

    def filter_variables(self, pattern, engine='regex'):
        return self._api.varslike(pattern, engine=engine)
    filter_variables.__doc__ = APIConnection.varslike.__doc__

    def _preprocess_variables(self, columns):
        if isinstance(columns, str):
            columns = [columns]
        return [col for this_pattern in columns for col in 
                self.filter_variables(this_pattern, engine='regex')]

    @property
    def _layer_lookup(self):
        """
        The lookup table relating the layers in the WMS service and the levels
        supported by this API product. 
        """
        pass

    @_layer_lookup.getter
    def _layer_lookup(self):
        raise NotImplementedError('This must be implemented on children '
                                  'of this class!')

    def from_place(self, place, variables=None,
                   level='tract', geometry_precision=2,
                   strict_within=True, return_bounds=False):
        """
        Query the Census for the given place. 

        Arguments
        ---------
        place               : str
                              description of the place. Should be of the form
                              "place, state" or "place"
        variables           : list or str
                              variable or set of variables to extract from the
                              API. Can include regex columns, which will match
                              to any column in the product. So, ['P001001', '^P002']
                              will match to P001001 and any column that starts with P002.
        level               : str (default: 'tract')
                              level at which to extract the geographic data. May be 
                              limited by some products to only involve tracts. 
        geometry_precision  : int (default: 2)
                              number of decimal places to preserve when getting the geometric
                              information around each observation in `level`.
        strict_within       : bool (default: True)
                              whether to retain only geometries that are fully within the 
                              target place. 
        return_bounds       : bool (default: False)
                              whether to return the boundary of the place being queried.
        """

        if variables is None:
            variables = ['NAME']

        name, state = place.split(',')
        place_ix, placematch = _fuzzy_match(name.strip(),
                                _places.query('STATE == "{}"'.format(state.strip()))
                                       .TARGETNAME)
        placerow = _places.loc[place_ix]

        env_idx, env_name = _fuzzy_match(placerow.TYPE,
                                         [layer.__repr__() for layer in
                                          self._api.mapservice.layers])

        env_layer = self._api.mapservice.layers[env_idx]

        placer = 'STATE={} AND PLACE={}'.format(placerow.STATEFP,
                                                placerow.TARGETFP)
        env = env_layer.query(where=placer)

        print('Matched: {} to {} '
              'within layer {}'.format(place,
                                       placematch.target,
                                       env_layer.__repr__().replace('(ESRILayer) ', '')))

        geoms, data = self._from_bbox(env.to_crs(epsg=4326).total_bounds,
                                      variables=variables, level=level,
                                      geometry_precision=geometry_precision,
                                      strict_within=False, return_bounds=False)
        if strict_within:
            geoms = geopandas.sjoin(geoms, env[['geometry']],
                                     how='inner', op='within')
        if return_bounds:
            return (geoms, data, env) 
        return geoms, data

    def _from_bbox(self, bounding_box, variables=None, level='tract',
                   geometry_precision=2, strict_within=False, return_bounds=False):

        env = geopandas.GeoDataFrame(geometry=[geometry.box(*bounding_box)])
        envelope = '%2C'.join(map(lambda x: '{:.6f}'.format(x), bounding_box))

        layer = self._api.mapservice.layers[self._layer_lookup[level]]
        involved = layer.query(geometryType='esriGeometryEnvelope',
                               geometry=envelope, returnGeometry='true', inSR=4326,
                               spatialRel='esriSpatialRelIntersects',
                               geometryPrecision=geometry_precision)
        if strict_within:
            involved = geopandas.sjoin(involved, env[['geometry']],
                                       how='inner', op='within')

        data = []
        if level == 'county':
            grouper = involved.groupby('STATE')
        else:
            grouper = involved.groupby(['STATE','COUNTY']) 
        for ix, chunk in grouper:
            if isinstance(ix, str):
                state = ix
            else:
                state, county = ix
            if level in ('county','state'):
                elements = chunk.COUNTY.unique()
            else:
                elements = chunk.TRACT.unique()
            n_elements = len(elements)
            def chunked_query(elements_in_chunk):
                geo_filter = dict(state=state)
                if level=='block':
                    geo_unit = 'block:*'
                    geo_filter['tract'] = ','.join(elements_in_chunk)
                    geo_filter['county'] = county
                elif level=='tract':
                    geo_unit = 'tract:{}'.format(','.join(elements_in_chunk))
                    geo_filter['county'] = county
                elif level=='county':
                    geo_unit = 'county:{}'.format(','.join(elements_in_chunk))
                elif level=='state':
                    geo_filter=None
                    geo_unit='state:{}'.format(','.join(elements_in_chunk))
                else:
                    raise Exception('Unrecognized level: {}'.format(level))

                return self._api.query(variables, geo_unit=geo_unit, geo_filter=geo_filter)

            n_chunks = numpy.ceil(n_elements / 500)
            data.append(pandas.concat([chunked_query(tracts_) for tracts_ in
                                      numpy.array_split(elements, n_chunks)],
                                      ignore_index=True, sort=False))
        data = pandas.concat((data), ignore_index=True, sort=False)

        for variable in variables:
            data[variable] = coerce(data[variable], float)

        if return_bounds:
            return involved, data, geopandas.GeoDataFrame(geometry=[geometry.box(*bounding_box)])
        return involved, data

    def _environment_from_layer(self, place, layername,
                                cache_name, geometry_precision):
        ix, name = _fuzzy_match(layername, [f.__repr__()
                                        for f in self._api.mapservice.layers])
        layer = self._api.mapservice.layers[ix]
        cache = getattr(self, cache_name, None)
        if cache is None:
            out_fields = 'BASENAME,GEOID'
            if 'Statistical' not in layername:
                out_fields += ',STATE'
            cache = layer.query(returnGeometry=False,
                                outFields=out_fields,
                                where='AREALAND>0')
            if 'Statistical' not in layername:
                _states = _ft('state')
                _states.columns = ['abbreviation', 'statefp', 'name']
                _states['STATE'] = _states.statefp.apply(lambda x: str(x).rjust(2, '0'))
                cache = cache.merge(_states[['abbreviation', 'STATE']],
                                    how='left', on='STATE')
                cache['BASENAME'] = cache[['BASENAME', 'abbreviation']].apply(lambda x:
                                                                      ', '.join(x), axis=1)
            self.__dict__[cache_name] = cache
        item_ix, item_name = _fuzzy_match(place, cache.BASENAME)
        print('Matched: {} to {} '
              'within layer {}'.format(place,
                                       item_name.target,
                                       layer.__repr__().replace('(ESRILayer) ', '')))
        row = cache.loc[item_ix]
        return layer.query(where='GEOID={}'.format(row.GEOID),
                           geometryPrecision=geometry_precision)

    def _from_name(self, place, variables, level,
                   layername, cache_name,
                   strict_within, return_bounds, geometry_precision):
        if variables is None:
            variables = []
        variables.append('NAME')
        env = self._environment_from_layer(place, layername,
                                           cache_name, geometry_precision)
        geoms, data = self._from_bbox(env.to_crs(epsg=4326).total_bounds,
                                      variables=variables, level=level,
                                      strict_within=False, return_bounds=False)
        if strict_within:
            geoms = geopandas.sjoin(geoms, env[['geometry']],
                                    how='inner', op='within')
        if return_bounds:
            return geoms, data, env
        return geoms, data

class Decennial2010(_Product):
    """The 2010 Decennial Census from the Census Bueau"""

    _layer_lookup = {'county': 100,
                     'tract': 14,
                     'block': 18}

    def __init__(self):
        super(Decennial2010, self).__init__()
        self._api = APIConnection('DECENNIALSF12010')
        self._api.set_mapservice('tigerWMS_Census2010')

    def _from_name(self, place, variables, level,
                   layername, cache_name,
                   strict_within=True,
                   return_bounds=False, geometry_precision=2):
        if level not in self._layer_lookup.keys():
            raise NotImplementedError('Only levels {} are supported. You provided {}.'
                                      'Try picking the state containing that level,'
                                      ' and then selecting from that data after it is'
                                      ' fetched'.format(level))
        if variables is None:
            variables = []
        variables.append('GEO_ID')
        variables = self._preprocess_variables(variables)

        caller = super(Decennial2010, self)._from_name
        geoms, variables, *rest = caller(place, variables, level,
                                         layername, cache_name,
                                         strict_within=strict_within,
                                         return_bounds=return_bounds,
                                         geometry_precision=geometry_precision)
        variables['GEOID'] = variables.GEO_ID.str.split('US').apply(lambda x: x[1])
        return_table = geoms[['GEOID', 'geometry']]\
                            .merge(variables.drop('GEO_ID', axis=1),
                                                  how='left', on='GEOID')
        if not return_bounds:
            return return_table
        else:
            return (return_table, *rest)

    def from_place(self, place, variables=None, level='tract',
                   strict_within=True, return_bounds=False):
        if variables is None:
            variables = []
        variables.append('GEO_ID')
        variables = self._preprocess_variables(variables)

        geoms, variables, *rest = super(Decennial2010, self)\
                                  .from_place(place, variables=variables, level=level,
                                              strict_within=strict_within,
                                              return_bounds=return_bounds)
        variables['GEOID'] = variables.GEO_ID.str.split('US').apply(lambda x: x[1])
        return_table = geoms[['GEOID', 'geometry']]\
                            .merge(variables.drop('GEO_ID', axis=1),
                                                  how='left', on='GEOID')
        if not return_bounds:
            return return_table
        else:
            return (return_table, *rest)
    from_place.__doc__ = _Product.from_place.__doc__

    def from_msa(self, name, variables=None, level='tract', **kwargs):
        return self._from_name(name, variables, level,
                               'Metropolitan Statistical Area', '_msas', **kwargs)
    from_msa.__doc__ = _Product.from_place.__doc__.replace('place', 'MSA')
    def from_csa(self, name, variables=None, level='tract', **kwargs):
        return self._from_name(name, variables, level,
                               'Combined Statistical Area', '_csas', **kwargs)
    from_csa.__doc__ = _Product.from_place.__doc__.replace('place', 'CSA')
    def from_county(self, name, variables=None, level='tract', **kwargs):
        return self._from_name(name, variables, level,
                               'Counties', '_counties', **kwargs)
    from_county.__doc__ = _Product\
                                    .from_place.__doc__\
                                    .replace('place', 'county')
    def from_state(self, name, variables=None, level='tract', **kwargs):
        return self._from_name(name, variables, level,
                               'States', '_states', **kwargs)
    from_state.__doc__ = _Product\
                                    .from_place.__doc__\
                                    .replace('place', 'state')

class ACS(_Product):

    _layer_lookup = {'county': 84,
                     'tract': 8}

    def __init__(self, year='latest'):
        if year == 'latest':
            year = 2018
        if year < 2013:
            raise NotImplementedError('The requested year {} is too early. '
                                      'Only 2013 and onwards is supported.'.format(year))
        self._api = APIConnection('ACSDT{}Y{}'.format(5, year)) 
        self._api.set_mapservice('tigerWMS_ACS{}'.format(year))
    
    def _from_name(self, place, variables, level,
                   layername, cache_name,
                   strict_within=True,
                   return_bounds=False, geometry_precision=2):
        if level not in self._layer_lookup().keys():
            raise NotImplementedError('Only levels {} are supported. You provided {}.'
                                      'Try picking the state containing that level,'
                                      ' and then selecting from that data after it is'
                                      ' fetched'.format(level))
        if level == 'block':
            raise ValueError('The American Community Survey is only administered'
                             ' at the blockgroup level or higher. Please select a'
                             ' level at or above the blockgroup level.')
        if variables is None:
            variables = []
        variables.append('GEO_ID')
        variables = self._preprocess_variables(variables)

        caller = super(ACS, self)._from_name
        geoms, variables, *rest = caller(place, variables, level,
                                         layername, cache_name,
                                         strict_within=strict_within,
                                         return_bounds=return_bounds,
                                         geometry_precision=geometry_precision)
        variables['GEOID'] = variables.GEO_ID.str.split('US').apply(lambda x: x[1])
        return_table = geoms[['GEOID', 'geometry']]\
                            .merge(variables.drop('GEO_ID', axis=1),
                                                  how='left', on='GEOID')
        if not return_bounds:
            return return_table
        else:
            return (return_table, *rest)
    
    def from_msa(self, name, variables=None, level='tract', **kwargs):
        return self._from_name(name, variables, level,
                               'Metropolitan Statistical Area', '_msas', **kwargs)
    from_msa.__doc__ = _Product.from_place.__doc__.replace('place', 'MSA')
    def from_csa(self, name, variables=None, level='tract', **kwargs):
        return self._from_name(name, variables, level,
                               'Combined Statistical Area', '_csas', **kwargs)
    from_csa.__doc__ = _Product.from_place.__doc__.replace('place', 'CSA')
    def from_county(self, name, variables=None, level='tract', **kwargs):
        return self._from_name(name, variables, level,
                               'Counties', '_counties', **kwargs)
    from_county.__doc__ = _Product\
                                    .from_place.__doc__\
                                    .replace('place', 'county')
    def from_state(self, name, variables=None, level='tract', **kwargs):
        return self._from_name(name, variables, level,
                               'States', '_states', **kwargs)
    from_state.__doc__ = _Product\
                                    .from_place.__doc__\
                                    .replace('place', 'state')
    
    def from_place(self, place, variables=None, level='tract',
                   strict_within=True, return_bounds=False):
        if variables is None:
            variables = []
        variables.append('GEO_ID')
        variables = self._preprocess_variables(variables)

        geoms, variables, *rest = super(ACS, self)\
                                  .from_place(place, variables=variables, level=level,
                                              strict_within=strict_within,
                                              return_bounds=return_bounds)
        variables['GEOID'] = variables.GEO_ID.str.split('US').apply(lambda x: x[1])
        return_table = geoms[['GEOID', 'geometry']]\
                            .merge(variables.drop('GEO_ID', axis=1),
                                                  how='left', on='GEOID')
        if not return_bounds:
            return return_table
        else:
            return (return_table, *rest)
    from_place.__doc__ =_Product.from_place.__doc__
    
def _fuzzy_match(matchtarget, matchlist):
    split = matchtarget.split(',')
    if len(split) == 2:
        target, state = split
    elif len(split) == 1:
        target = split[0]
    else:
        raise AssertionError('Uncertain place identifier {}. The place identifier should '
                             'look something like "placename, state" or, for larger areas, '
                             'like Combined Statistical Areas or Metropolitan Statistical Areas,'
                             'placename1-placename2, state1-state2-state3'.format(target))

    table = pandas.DataFrame({'target':matchlist})
    table['score'] = table.target.apply(lambda x: fuzz.partial_ratio(target.strip(), x))
    if len(split) == 1:
        if (table.score == table.score.max()).sum() > 1:
            ixmax, rowmax = _break_ties(matchtarget, table)
        else:
            ixmax = table.score.idxmax()
            rowmax = table.loc[ixmax]
        return ixmax, rowmax
    
    in_state = table.target.str.endswith(state.strip())

    assert any(in_state), ('State {} is not found from place {}. '
                           'Should be a standard Census abbreviation, like'
                           ' CA, AZ, NC, or PR'.format(state, matchtarget))
    table = table[in_state]
    if (table.score == table.score.max()).sum() > 1:
        ixmax, rowmax = _break_ties(matchtarget, table)
    else:
        ixmax = table.score.idxmax()
        rowmax = table.loc[ixmax]
    return ixmax, rowmax

def coerce(column, kind):
    """
    Converty type of column to kind, or keep column unchanged
    if that conversion fails.
    """
    try:
        return column.astype(kind)
    except ValueError:
        return column

def _break_ties(matchtarget, table):
    split = matchtarget.split(',')
    if len(split) == 2:
        target, state = split
    else: 
        target = split[0]
    table['score2'] = table.target.apply(lambda x: fuzz.ratio(target.strip(), x))
    among_winners = table[table.score == table.score.max()]
    double_winners = among_winners[among_winners.score2 == among_winners.score2.max()]
    if double_winners.shape[0] > 1:
        ixmax = double_winners.score2.idxmax()
        ixmax_row = double_winners.loc[ixmax]
        warn('Cannot disambiguate placename {}. Picking the shortest, best '
             'matched placename, {}, from {}'.format(matchtarget, ixmax_row.target.item(),
                                                     ', '.join(double_winners.target.tolist())))
        return ixmax, ixmax_row
    ixmax = double_winners.score2.idxmax()
    return ixmax, double_winners.loc[ixmax]
