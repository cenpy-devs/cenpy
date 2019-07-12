from .remote import APIConnection
from .explorer import fips_table as _ft
from shapely import geometry
from fuzzywuzzy import fuzz
from warnings import warn
import geopandas
import pandas
import numpy
import copy

_places = _ft('place')
_places['TARGETFP'] = _places.PLACEFP.apply(lambda x: str(x).rjust(5, '0'))
_places['TARGETNAME'] = _places.PLACENAME
_places['STATEFP'] = _places.STATEFP.apply(lambda x: str(x).rjust(2, '0'))
_places.drop(['PLACEFP', 'FUNCSTAT', 'COUNTY', 'PLACENAME'], inplace=True, axis=1)

__all__ = ['Decennial2010', 'ACS']

_ACS_MISSING = (-999999999, -888888888, -666666666,
                -555555555, -333333333, -222222222)

class _Product(object):
    """The fundamental building block to make pre-configured Census Products, like ACS or Decennial2010."""

    def __repr__(self):
        return self._api.__repr__()

    @property
    def variables(self):
        """All variables, including columns and search predictates,
         available from the API"""
        return self._api.variables.sort_index()
    
    @property
    def tables(self):
        """
        All of the main table codes in the Census API for this product. 
        
        These *do not* include crosstabulations, like "Sex by Age (White Alone)",
        whose table numbers end in characters (like B01001A)
        """
        pass

    @tables.getter
    def tables(self):
        """
        All of the main table codes in the Census API for this product. 
        
        These *do not* include crosstabulations, like "Sex by Age (White Alone)",
        whose table numbers end in characters (like B01001A)
        """
        raise NotImplementedError('This must be implemented on children of this class!')

    def filter_variables(self, pattern=None, by=None, engine='re'):
        return self._api.varslike(pattern=pattern, by=by, engine=engine)
    filter_variables.__doc__ = APIConnection.varslike.__doc__

    def filter_tables(self, pattern=None, by=None, engine='re'):
        """
        Filter tables by a given pattern. Consult filter_variables for options.
        """
        return self._api.varslike(pattern=pattern, by=by, engine=engine, 
                                  within=self.tables)

    def _preprocess_variables(self, columns):
        if isinstance(columns, str):
            columns = [columns]
        expanded = [col for this_pattern in columns for col in
                    self.filter_variables(this_pattern, engine='regex').index]
        return numpy.unique(expanded).tolist()

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

    def from_place(self, place, variables=None, place_type=None,
                   level='tract', return_geometry=True,
                   geometry_precision=2,
                   strict_within=True, return_bounds=False,
                   replace_missing=True):
        """
        Query the Census for the given place. 

        Parameters
        ---------
        place               : str
                              description of the place. Should be of the form
                              "place, state" or "place"
        place_type          : str
                              type of place to focus on, Incorporated Place, County Subdivision, or Census Designated Place. 
        variables           : list or str
                              variable or set of variables to extract from the
                              API. Can include regex columns, which will match
                              to any column in the product. So, ['P001001', '^P002']
                              will match to P001001 and any column that starts with P002.
        level               : str (default: 'tract')
                              level at which to extract the geographic data. May be
                              limited by some products to only involve tracts. (default: 'tract')
        return_geometry     : bool
                              whether to return the geometries of the queried records. True by default, this will ensure
                              that the return type of from_place is a geopandas.GeoDataFrame. If False, then only the 
                              records are fetched; none of the records' geometries are requested from the server. (default: True) 
        geometry_precision  : int 
                              number of decimal places to preserve when getting the geometric
                              information around each observation in `level`. (default: 2)
        strict_within       : bool
                              whether to retain only geometries that are fully within the
                              target place.
        return_bounds       : bool 
                              whether to return the boundary of the place being queried. (default: False)
        replace_missing     : bool 
                              whether to replace missing values in the data with numpy.nan,
                              according to the standard missing values used by the ACS. (default: True)
        
        Notes
        ------

        You should always try to provide a place_type. There is a significant amount of vagueness in what is meant
        by "place" that you may not get the match you intend if you do not provide a place_type.
        """

        if variables is None:
            variables = ['NAME']
        
        name = place.split(',')
        assert isinstance(name, list)
        if len(name) < 2:
            warn('Uncertain place identifier "{}". The place identifier should '
                 'look something like "placename, state" or, for larger areas, '
                 'like Combined Statistical Areas or Metropolitan Statistical Areas,'
                 '"placename1-placename2, state1-state2-state3"'.format(place), stacklevel=2)


        if(place_type != None):
            if(place_type in ['Census Designated Place', 'Incorporated Place',
                              'County Subdivision']):
                searchtarget = _places[_places['TYPE']==place_type]
            else:
                raise Exception('place_type must be on of Census Designated Place, Incorporated Place, County Subdivision')
        else:
            searchtarget = _places.assign(TypeOrder = _places['TYPE'].apply(lambda x : {}) )

        if len(name) == 2:
            name, state = name
            searchtarget = searchtarget.assign(state=_places.STATE.str.lower())\
                                  .query('state == "{}"'.format(state.strip().lower()))\
                                  .TARGETNAME
        elif len(name) == 1:
            name = name[0]
            searchtarget = searchtarget.TARGETNAME
        else:
            raise Exception()

        placematch = _fuzzy_match(name.strip(), searchtarget)
        placerow = _places.loc[placematch.name]

        env_name = _fuzzy_match(placerow.TYPE, [layer.__repr__() for layer in
                                self._api.mapservice.layers])

        env_layer = self._api.mapservice.layers[env_name.name]
        if place_type == 'County Subdivision':
            placer = 'STATE={} AND COUSUB={}'.format(placerow.STATEFP,
                                                    placerow.TARGETFP)
        else:

            placer = 'STATE={} AND PLACE={}'.format(placerow.STATEFP,
                                                    placerow.TARGETFP)
        env = env_layer.query(where=placer)

        print('Matched: {} to {} '
              'within layer {}'.format(place,
                                       placematch.target,
                                       env_layer.__repr__().replace('(ESRILayer) ', '')))

        geoms, data = self._from_bbox(env.to_crs(epsg=4326).total_bounds,
                                      variables=variables, level=level,
                                      return_geometry=return_geometry,
                                      geometry_precision=geometry_precision,
                                      strict_within=False, return_bounds=False,
                                      replace_missing=replace_missing)
        if strict_within:
            geoms = geopandas.sjoin(geoms, env[['geometry']],
                                     how='inner', op='within')
        if return_bounds:
            return (geoms, data, env)
        return geoms, data

    def _from_bbox(self, bounding_box, variables=None, level='tract', return_geometry=True,
                   geometry_precision=2, strict_within=False, return_bounds=False, 
                   replace_missing=True):
        """
        This is an internal method to handle querying the Census API and the GeoAPI using
        bounding boxes. This first gets the target records in the given level that fall within
        the provided bounding box using the GeoAPI. Then, it gets the variables for each record
        from the Census API. 
        """

        # Regularize the bounding box for the web request
        env = geopandas.GeoDataFrame(geometry=[geometry.box(*bounding_box)])
        envelope = '%2C'.join(map(lambda x: '{:.6f}'.format(x), bounding_box))

        layer = self._api.mapservice.layers[self._layer_lookup[level]]
        involved = layer.query(geometryType='esriGeometryEnvelope',
                               geometry=envelope, 
                               returnGeometry='true',
                               inSR=4326,
                               spatialRel='esriSpatialRelIntersects',
                               geometryPrecision=geometry_precision)
        # filter the records by a strict "within" query if needed
        if strict_within:
            involved = geopandas.sjoin(involved, env[['geometry']],
                                       how='inner', op='within')
        
        # Construct a "query" translator between the GeoAPI and the Census API
        # in chunks using a closure around chunked_query. 
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
            
            # Run each of these chunks of the query in order to avoid requesting too much data. 
            n_chunks = numpy.ceil(n_elements / 500)
            data.append(pandas.concat([chunked_query(tracts_) for tracts_ in
                                      numpy.array_split(elements, n_chunks)],
                                      ignore_index=True, sort=False))
        data = pandas.concat((data), ignore_index=True, sort=False)
       
        if replace_missing:
            for variable in variables:
                data[variable] = _replace_missing(_coerce(data[variable], float))

        if return_geometry:
            data = geopandas.GeoDataFrame(data)

        if return_bounds:
            return involved, data, geopandas.GeoDataFrame(geometry=[geometry.box(*bounding_box)])

        return involved, data

    def _environment_from_layer(self, place, layername, geometry_precision, 
                                cache_name=None):
        """
        A helper function to extract the right "container", or "environment" to
        conduct a query against. 
        """
        layername_match = _fuzzy_match(layername, [f.__repr__()
                                        for f in self._api.mapservice.layers])
        layer = self._api.mapservice.layers[layername_match.name]
        item_name, table = self.check_match(place, layername, cache_name=cache_name, 
                                            return_table=True)
        if cache_name is None:
            cache_name = layername_match.target.lstrip('(ESRILayer) ')
        row = self._cache[cache_name].loc[item_name.name]
        return layer.query(where='GEOID={}'.format(row.GEOID),
                           geometryPrecision=geometry_precision)

    def _from_name(self, place, variables, level,
                   layername, strict_within, return_bounds, 
                   geometry_precision, cache_name=None, replace_missing=True, 
                   return_geometry=True):
        """
        A helper function, internal to the product, which pieces together the 
        construction of a bounding box (from environment_from_layer) and 
        the querying of the GeoAPI using that bounding box in (from_bbox)
        """
        if variables is None:
            variables = []
        else:
            variables = copy.copy(variables)
        variables.append('NAME')
        env = self._environment_from_layer(place, layername, geometry_precision, 
                                           cache_name=cache_name)
        geoms, data = self._from_bbox(env.to_crs(epsg=4326).total_bounds,
                                      variables=variables, level=level,
                                      strict_within=False, return_bounds=False,
                                      replace_missing=replace_missing)
        if strict_within:
            geoms = geopandas.sjoin(geoms, env[['geometry']],
                                    how='inner', op='within')
        if return_bounds:
            return geoms, data, env
        return geoms, data

    def check_match(self, name, level, return_level=False, return_table=False, cache_name=None):
        """
        A helper function to verify the match used by the product API. 

        Parameters
        ----------
        name        : str
                      the name of the place/query string to be searched. Should be in the form
                      "placename, stateabbreviation" (like "Los Angeles, CA"). For multiply-named
                      locations, the format should be town1-town2, state1-state2, like Kansas City, KS-MO. 
        level       : str
                      the name of the census hierarchy in which the name should be searched. Should be
                      something like "Incorporated Places" or "States". 
        return_level: bool
                      Whether to return the level match. If you are uncertain as to which level the name
                      is matching, set this flag to `True` to see the Census API layer that matches. 
        return_table: bool
                      Whether to return the full table of possible matches for the queried name or level. 
                      If this is true, the return values are converted to be tuples, containing (match, table),
                      where "match" is the entity in the Census API that matches the requested name or level,
                      and table is the set of *all* possible values that could have been matched. If the matching
                      fails for your first run, try inspecting table using return_table=True. Find the place/name
                      you intend to match, and then input exactly that string. 
        Returns
        -------
        int
            the row of the match table that records the matched name. 
            If return_table is True, this becomes a tuple of (row, table). 
            If return_level is True, the result is returned for both the match on the name and on the level.
            If both return_table and return_level are true, then two tuples are returned. The first contains the
            match for the name and the full table of possible names, and the second contains the match of the level and 
        the full table of possible levels. 

        Notes
        -----
        matches are made based on the `partial_ratio` and `ratio` scorings from the fuzzywuzzy package. The `partial_ratio` 
        prioritizes the "target" being fully contained in the match. So, a string like `Chicago, IL` would be a perfect 
        match for `Chicago, IL` as well as 'North Chicago, IL' or `Chicago Heights, IL`. If there are ties (which happens often),
        the `ratio` percentage is used to break them. This considers the full string similarity, so that the closest
        full strings are matched. This ensures that `Chicago, IL` is matched to `Chicago, IL`, and not `West Chicago, IL`. 

        Consult the fuzzywuzzy package documentation for more information on the `partial_ratio`
        and `ratio` matches. 

        """
        layer_result = _fuzzy_match(level, [f.__repr__() for f in self._api.mapservice.layers], 
                                   return_table=return_table)
        if return_table:
            layer_name, layer_matchtable = layer_result
        else:
            layer_name = layer_result
        layer_ix = layer_name.name
        if cache_name is None:
            cache_name = layer_name.target.lstrip('(ESRILayer) ')
        cache = self._cache.get(cache_name, None)
        if cache is None:
            layer = self._api.mapservice.layers[layer_ix]
            out_fields = 'BASENAME,GEOID'
            if 'Statistical' not in layer_name.target:
                out_fields += ',STATE'
            cache = layer.query(returnGeometry='false',
                                outFields=out_fields,
                                where='AREALAND>0')
            if 'Statistical' not in layer_name.target:
                _states = _ft('state')
                _states.columns = ['abbreviation', 'statefp', 'name']
                _states['STATE'] = _states.statefp.apply(lambda x: str(x).rjust(2, '0'))
                cache = cache.merge(_states[['abbreviation', 'STATE']],
                                    how='left', on='STATE')
                cache['BASENAME'] = cache[['BASENAME', 'abbreviation']].apply(lambda x:
                                                                      ', '.join(x), axis=1)
            self._cache.update({cache_name: cache})
        result = _fuzzy_match(name, cache.BASENAME, return_table=return_table)
        if return_level:
            return result, layer_result
        else:
            return result


class Decennial2010(_Product):
    """The 2010 Decennial Census from the Census Bueau"""
    _layer_lookup = {'county': 100,
                     'tract': 14,
                     'block': 18}

    def __init__(self):
        super(Decennial2010, self).__init__()
        self._api = APIConnection('DECENNIALSF12010')
        self._api.set_mapservice('tigerWMS_Census2010')
        self._cache = dict()

    def _from_name(self, place, variables, level,
                   layername, 
                   return_geometry=True,
                   cache_name=None,
                   strict_within=True,
                   return_bounds=False, geometry_precision=2):
        if level not in self._layer_lookup.keys():
            raise NotImplementedError('Only levels {} are supported. You provided {}.'
                                      'Try picking the state containing that level,'
                                      ' and then selecting from that data after it is'
                                      ' fetched'.format(level))
        if variables is None:
            variables = []
        else:
            variables = copy.copy(variables)
        variables = self._preprocess_variables(variables)
        variables.append('GEO_ID')

        caller = super(Decennial2010, self)._from_name
        geoms, variables, *rest = caller(place, variables, level,
                                         layername, cache_name=cache_name,
                                         return_geometry=return_geometry,
                                         strict_within=strict_within,
                                         return_bounds=return_bounds,
                                         geometry_precision=geometry_precision)
        variables['GEOID'] = variables.GEO_ID.str.split('US').apply(lambda x: x[1])
        return_table = geoms[['GEOID', 'geometry']]\
                            .merge(variables.drop('GEO_ID', axis=1),
                                                  how='left', on='GEOID')
        if return_geometry is False:
            return_table = pandas.DataFrame(return_table.drop(return_table.geometry.name, axis=1))
        if not return_bounds:
            return return_table
        else:
            return (return_table, *rest)

    def from_place(self, place, variables=None, level='tract', 
                   return_geometry=True,
                   place_type=None,
                   strict_within=True, return_bounds=False,
                   replace_missing=True):
        if variables is None:
            variables = []
        else:
            variables = copy.copy(variables)
        variables = self._preprocess_variables(variables)
        variables.append('GEO_ID')

        geoms, variables, *rest = super(Decennial2010, self)\
                                  .from_place(place, variables=variables, level=level,
                                              return_geometry=return_geometry,
                                              place_type=place_type,
                                              strict_within=strict_within,
                                              return_bounds=return_bounds,
                                              replace_missing=replace_missing)
        variables['GEOID'] = variables.GEO_ID.str.split('US').apply(lambda x: x[1])
        return_table = geoms[['GEOID', 'geometry']]\
                            .merge(variables.drop('GEO_ID', axis=1),
                                                  how='left', on='GEOID')
        if return_geometry is False:
            return_table = pandas.DataFrame(return_table.drop(return_table.geometry.name, axis=1))
        if not return_bounds:
            return return_table
        else:
            return (return_table, *rest)
    from_place.__doc__ = _Product.from_place.__doc__

    def from_msa(self, msa, variables=None, level='tract', **kwargs):
        return self._from_name(msa, variables, level,
                               'Metropolitan Statistical Area', **kwargs)
    from_msa.__doc__ = _Product.from_place.__doc__.replace('place', 'MSA')
    def from_csa(self, csa, variables=None, level='tract', **kwargs):
        return self._from_name(csa, variables, level,
                               'Combined Statistical Area', **kwargs)
    from_csa.__doc__ = _Product.from_place.__doc__.replace('place', 'CSA')
    def from_county(self, county, variables=None, level='tract', **kwargs):
        return self._from_name(county, variables, level,
                               'Counties', **kwargs)
    from_county.__doc__ = _Product\
                                    .from_place.__doc__\
                                    .replace('place', 'county')
    def from_state(self, state, variables=None, level='tract', **kwargs):
        return self._from_name(state, variables, level,
                               'States', **kwargs)
    from_state.__doc__ = _Product\
                                    .from_place.__doc__\
                                    .replace('place', 'state')\
                                    .replace('"state, state" or "state"', '"state, abbreviation" or "state"')
    
    @property
    def tables(self):
        """
        All of the main table codes in the Census API for this product. 
        
        These *do not* include crosstabulations, like "Sex by Age (White Alone)",
        whose table numbers end in characters (like B01001A)
        """
        pass
    
    @tables.getter
    def tables(self):
        """
        All of the main table codes in the Census API for this product. 
        
        These *do not* include crosstabulations, like "Sex by Age (White Alone)",
        whose table numbers end in characters (like B01001A)
        """
        try:
            return self._tables
        except AttributeError:
            groups = self.variables.groupby('group')
            unique_concepts = groups.concept.unique()
            
            single_unique_concepts = unique_concepts[unique_concepts.apply(len) == 1]

            self._stems = single_unique_concepts.apply(lambda x: x[0]).to_frame('description')
            self._stems['columns'] = groups.apply(lambda x: x.index.tolist())
            
            is_table = numpy.asarray([_can_int(x[-1]) for x in self._stems.index])
            self._tables = self._stems[is_table]
            self._crosstabs = self._stems[~is_table]
            
            return self._tables

    @property
    def crosstab_tables(self):
        """
        All of the crosstab table codes in the Census API for this product. 
        
        These *do not* include main tables, like "Race", whose table numbers
        end in integers (like B02001).
        """
        pass

    @crosstab_tables.getter
    def crosstab_tables(self):
        """
        All of the crosstab table codes in the Census API for this product. 
        
        These *do not* include main tables, like "Race", whose table numbers
        end in integers (like B02001).
        """
        try:
            return self._crosstabs
        except AttributeError:
            _ = self.tables #compute the divisions
            return self._crosstabs


class ACS(_Product):
    """The American Community Survey (5-year vintages) from the Census Bueau"""

    _layer_lookup = {'county': 84,
                     'tract': 8}

    def __init__(self, year='latest'):
        self._cache = dict()
        if year == 'latest':
            year = 2017
        if year < 2013:
            raise NotImplementedError('The requested year {} is too early. '
                                      'Only 2013 and onwards is supported.'.format(year))
        self._api = APIConnection('ACSDT{}Y{}'.format(5, year))
        self._api.set_mapservice('tigerWMS_ACS{}'.format(year))

    def _from_name(self, place, variables, level,
                   layername, 
                   return_geometry=True,
                   cache_name=None,
                   strict_within=True,
                   return_bounds=False, geometry_precision=2):
        if level not in self._layer_lookup.keys():
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
        else:
            variables = copy.copy(variables)
        variables = self._preprocess_variables(variables)
        variables.append('GEO_ID')

        caller = super(ACS, self)._from_name
        geoms, variables, *rest = caller(place, variables, level,
                                         layername, 
                                         return_geometry=return_geometry,
                                         cache_name=cache_name,
                                         strict_within=strict_within,
                                         return_bounds=return_bounds,
                                         geometry_precision=geometry_precision)
        variables['GEOID'] = variables.GEO_ID.str.split('US').apply(lambda x: x[1])
        return_table = geoms[['GEOID', 'geometry']]\
                            .merge(variables.drop('GEO_ID', axis=1),
                                                  how='left', on='GEOID')
        if return_geometry is False:
            return_table = pandas.DataFrame(return_table.drop(return_table.geometry.name, axis=1))
        if not return_bounds:
            return return_table
        else:
            return (return_table, *rest)

    def from_msa(self, msa, variables=None, level='tract', **kwargs):
        return self._from_name(msa, variables, level,
                               'Metropolitan Statistical Area', **kwargs)
    from_msa.__doc__ = _Product.from_place.__doc__.replace('place', 'MSA')
    def from_csa(self, csa, variables=None, level='tract', **kwargs):
        return self._from_name(csa, variables, level,
                               'Combined Statistical Area', **kwargs)
    from_csa.__doc__ = _Product.from_place.__doc__.replace('place', 'CSA')
    def from_county(self, county, variables=None, level='tract', **kwargs):
        return self._from_name(county, variables, level, 'Counties', **kwargs)
    from_county.__doc__ = _Product\
                                    .from_place.__doc__\
                                    .replace('place', 'county')
    def from_state(self, state, variables=None, level='tract', **kwargs):
        return self._from_name(state, variables, level, 'States', **kwargs)
    from_state.__doc__ = _Product\
                                    .from_place.__doc__\
                                    .replace('place', 'state')\
                                    .replace('"state, state" or "state"', '"state, abbreviation" or "state"')
    
    def from_place(self, place, variables=None, level='tract',
                   return_geometry=True,
                   place_type=None,
                   strict_within=True, return_bounds=False,
                   replace_missing=True):
        if variables is None:
            variables = []
        else:
            variables = copy.copy(variables)
        variables = self._preprocess_variables(variables)
        variables.append('GEO_ID')

        geoms, variables, *rest = super(ACS, self)\
                                  .from_place(place, variables=variables, level=level,
                                              return_geometry=return_geometry,
                                              place_type=place_type,
                                              strict_within=strict_within,
                                              return_bounds=return_bounds,
                                              replace_missing=replace_missing)
        variables['GEOID'] = variables.GEO_ID.str.split('US').apply(lambda x: x[1])
        return_table = geoms[['GEOID', 'geometry']]\
                            .merge(variables.drop('GEO_ID', axis=1),
                                                  how='left', on='GEOID')
        if return_geometry is False:
            return_table = pandas.DataFrame(return_table.drop(return_table.geometry.name, axis=1))
        if not return_bounds:
            return return_table
        else:
            return (return_table, *rest)
    from_place.__doc__ =_Product.from_place.__doc__
    
    @property
    def tables(self):
        """
        All of the main table codes in the Census API for this product. 
        
        These *do not* include crosstabulations, like "Sex by Age (White Alone)",
        whose table numbers end in characters (like B01001A)
        """
        pass
    
    @tables.getter
    def tables(self):
        """
        All of the main table codes in the Census API for this product. 
        
        These *do not* include crosstabulations, like "Sex by Age (White Alone)",
        whose table numbers end in characters (like B01001A)
        """
        try:
            return self._tables
        except AttributeError:
            splits = pandas.Series(self.variables.index.str.split('_'))
            grouper = self.variables.assign(split_len=splits.apply(len).values, 
                                          table_name=splits.apply(lambda x: x[0]).values)\
                                  .query('split_len == 2')\
                                  .groupby('table_name')
            stems = grouper.concept.unique().to_frame('description')
            stems['columns'] = grouper.apply(lambda x: x.index.copy().tolist())
            assert stems.description.apply(len).unique() == 1, 'some variables have failed to parse into tables'
            stems['description'] = stems.description.apply(lambda x: x[0])
            result = stems.drop('GEO', axis=0, errors='ignore')
            self._stems = result
            # keep around the main tables only if they're not crosstabs (ending in alphanumeric)
            self._tables = result.loc[[ix for ix in result.index if _can_int(ix[-1])]]
            return self._tables

    @property
    def crosstab_tables(self):
        """
        All of the crosstab table codes in the Census API for this product. 
        
        These *do not* include main tables, like "Race", whose table numbers
        end in integers (like B02001).
        """
        pass

    @crosstab_tables.getter
    def crosstab_tables(self):
        """
        All of the crosstab table codes in the Census API for this product. 
        
        These *do not* include main tables, like "Race", whose table numbers
        end in integers (like B02001).
        """
        try:
            return self._crosstabs
        except AttributeError:
            tables = self.tables # needs to be instantiated first
            self._crosstabs = self._stems.loc[self._stems.index.difference(tables.index)]
            return self._crosstabs

#############
# UTILITIES #
#############

def _fuzzy_match(matchtarget, matchlist, return_table=False):
    """
    Conduct a fuzzy match with matchtarget, within the list of possible match candidates in matchlist. 

    Parameters
    ---------
    matchtarget :   str
                 a string to be matched to a set of possible candidates
    matchlist   :   list of str
                 a list (or iterable) containing strings we are interested in matching
    return_table:   bool
                 whether to return the full table of scored candidates, or to return only the single
                 best match. If False (the default), only the best match is returned.
    
    Notes
    -----
    consult the docstring for Product.check_match for more information on how the actual matching
    algorithm works. 
    """
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
    table['score'] = table.target\
                          .apply(lambda x: fuzz.partial_ratio(target.strip().lower(),
                                                              x.lower()))
    if len(split) == 1:
        if (table.score == table.score.max()).sum() > 1:
            ixmax, rowmax = _break_ties(matchtarget, table)
        else:
            ixmax = table.score.idxmax()
            rowmax = table.loc[ixmax]
        if return_table:
            return rowmax, table.sort_values('score')
        return rowmax

    in_state = table.target.str.lower().str.endswith(state.strip().lower())

    assert any(in_state), ('State {} is not found from place {}. '
                           'Should be a standard Census abbreviation, like'
                           ' CA, AZ, NC, or PR'.format(state, matchtarget))
    table = table[in_state]
    if (table.score == table.score.max()).sum() > 1:
        ixmax, rowmax = _break_ties(matchtarget, table)
    else:
        ixmax = table.score.idxmax()
        rowmax = table.loc[ixmax]
    if return_table:
        return rowmax, table.sort_values('score')
    return rowmax

def _coerce(column, kind):
    """
    Converty type of column to kind, or keep column unchanged
    if that conversion fails.
    """
    try:
        return column.astype(kind)
    except ValueError:
        return column

def _replace_missing(column, missings=_ACS_MISSING):
    """
    replace ACS missing values using numpy.nan. 
    """
    for val in _ACS_MISSING:
        column.replace(val, numpy.nan, inplace=True)
    return column

def _break_ties(matchtarget, table):
    """
    break ties in the fuzzy matching algorithm using a second scoring method 
    which prioritizes full string matches over substring matches.  
    """
    split = matchtarget.split(',')
    if len(split) == 2:
        target, state = split
    else:
        target = split[0]
    table['score2'] = table.target.apply(lambda x: fuzz.ratio(target.strip().lower(),
                                                              x.lower()))
    among_winners = table[table.score == table.score.max()]
    double_winners = among_winners[among_winners.score2 == among_winners.score2.max()]
    if double_winners.shape[0] > 1:
        ixmax = double_winners.score2.idxmax()
        ixmax_row = double_winners.loc[ixmax]
        warn('Cannot disambiguate placename {}. Picking the shortest, best '
             'matched placename, {}, from {}'.format(matchtarget, ixmax_row.target,
                                                     ', '.join(double_winners.target.tolist())))
        return ixmax, ixmax_row
    ixmax = double_winners.score2.idxmax()
    return ixmax, double_winners.loc[ixmax]

def _can_int(char):
    """check if a character can be turned into an integer"""
    try:
        int(char)
        return True
    except ValueError:
        return False
