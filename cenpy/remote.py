import pandas as pd
from json import JSONDecodeError
import requests as r
import numpy as np
from . import explorer as exp
from . import tiger as tig
import math
from six import iteritems, PY3

if PY3:
    unicode = str

class ParseException(Exception):
    def __init__(self, *args, response=None):
        Exception.__init__(self, *args)
        self.response = response

class APIConnection():
    """The fundamental building block for US Census Bureau data API Endpoints"""
    def __init__(self, api_name=None, apikey=''):
        """
        Constructor for a Connection object

        Parameters
        ------------
        api_name : str
                   shortcode identifying which api to connect to
        api_key  : str
                   US Census bureau API key
        """
        if 'eits' not in api_name and api_name is not None:
            try:
                curr = exp.APIs[api_name]
            except KeyError:
                raise KeyError('The requested Census Product shortcode ({}) was not found in the '
                               'list of API shortcodes. Please check cenpy.explorer.available()'
                               ' to determine whether the API shortcode you have requested is correct.'.format(api_name))
            self.title = curr['title']
            self.identifier = curr['identifier']
            self.description = curr['description']
            self.cxn = unicode(curr['distribution'][0]['accessURL'] + '?')
            self.last_query = ''
            if apikey == '':
                from .tools import _load_sitekey
                apikey = _load_sitekey()
                if apikey is None:
                    apikey = ''
            self.apikey = apikey

            self.__urls__ = {
                k.strip('c_')[:-4]: v for k, v in iteritems(curr) if k.endswith('Link')}

            if 'documentation' in self.__urls__.keys():
                self.doclink = self.__urls__['documentation']
            if 'variables' in self.__urls__.keys():
                v = pd.DataFrame()
                variables = r.get(self.__urls__['variables'])
                variables.raise_for_status()

                self.variables = v.from_dict(variables.json()['variables']).T
            if 'geography' in self.__urls__.keys():
                res = r.get(self.__urls__['geography'])
                res.raise_for_status()
                res = res.json()
                self.geographies = {k: pd.DataFrame().from_dict(v) for k, v
                                    in iteritems(res)}
            if 'tags' in self.__urls__.keys():
                try:
                    tags = r.get(self.__urls__['tags'])
                    tags.raise_for_status()
                    self.tags = list(tags.json().values())[0]
                except r.HTTPError:
                    pass

            if 'examples' in self.__urls__.keys():
                try:
                    examples = r.get(self.__urls__['examples'])
                    examples.raise_for_status()
                    self.example_entries = examples.json()
                except r.HTTPError:
                    pass

        elif 'eits' in api_name:
            raise NotImplementedError(
                'EITS datasets are not supported at this time')
        else:
            raise ValueError(
                'Pick dataset identifier using the cenpy.explorer.available() function')

    def __repr__(self):
        if hasattr(self, 'mapservice'):
            return str('Connection to ' + self.title + '(ID: ' +
                       self.identifier + ')' + '\nWith MapServer: ' +
                       self.mapservice.title)
        else:
            return str('Connection to ' + self.title + ' (ID: ' +
                       self.identifier + ')')

    def explain(self, *args, verbose=True):
        """
        Explain a column or list of columns.

        Parameters
        ------------
        *args : str or sequence of strs
                name or list of names for columns in the `variables` dataframe that require
                explanation. lists will be unpacked by default. 
        verbose : bool
                  whether to grab both "label" and "concept" from the variable dataframe.
                  (default: True)

        Returns
        ----------
        dictionary of explanatory texts about variables inputted.
        """
        grab = ['concept']
        if not verbose:
            grab = ['label']
        if isinstance(args[0], list) and len(args) == 1:
            args = args[0]
        try:
            return {arg: self.variables.ix[arg][grab].values[0] for arg in args}
        except TypeError:
            raise TypeError(
                "Cannot flatten your search into one list. Please consolidate search terms into one list, or provide each term as a separate argument.")

    def query(self, cols=None, geo_unit='', geo_filter={}, apikey='', **kwargs):
        """
        Conduct a query over the USCB api connection

        Parameters
        -----------
        cols : list of str
               census column names to request
        geo_unit : dict or str 
                   identifiers for the basic spatial unit of the query
        geo_filter : dict 
                     required geometries above the specified geo_unit needed 
                     to complete the query
        apikey : str
                 USCB-issued API key for your query.
        **kwargs : additional search predicates can be passed here

        Returns
        --------
        pandas.DataFrame
            results from the API

        Example
        --------
        To grab the total population of all of the census blocks in a part of Arizona:

            >>> cxn.query('P0010001', geo_unit = 'block:*', geo_filter = {'state':'04','county':'019','tract':'001802'})

        Notes
        ------

        If your list of columns exceeds the maximum query length of 50,
        the query will be broken up and concatenated back together at
        the end. Sometimes, the USCB might frown on large-column queries,
        so be careful with this. Cenpy is not liable for your key getting
        banned if you query tens of thousands of columns at once.
        """
        assert (not (cols is None)), 'Columns must be provided for query!'

        if not geo_unit and 'geo_unit' in self.variables.index:
            geo_unit = 'us:00'

        if len(cols) >= 50:
            return self._bigcolq(cols, geo_unit, geo_filter, apikey, **kwargs)

        self.last_query = self.cxn

        self.last_query += 'get=' + ','.join(col for col in cols)
        convert_numeric = kwargs.pop('convert_numeric', True)
        index = kwargs.pop('index', '')

        if geo_unit:
            self.last_query += '&for=' + geo_unit

        if geo_filter != {}:
            self.last_query += '&in='
            self.last_query += '+'.join([':'.join(kvpair)
                                         for kvpair in iteritems(geo_filter)])

        if apikey != '':
            self.last_query += '&key=' + apikey
        elif self.apikey != '':
            self.last_query += '&key=' + self.apikey

        if kwargs != {}:
            self.last_query += ''.join(['&{k}={v}'.format(k=k, v=v)
                                        for k, v in iteritems(kwargs)])

        res = r.get(self.last_query)
        if res.status_code == 204:
            raise r.HTTPError(' '.join((str(res.status_code),
                                       'error: no records matched your query')))
        try:
            json_content = res.json()
            df = pd.DataFrame().from_records(json_content[1:],
                                             columns=json_content[0])
            assert all([col in df.columns for col in cols])
            if convert_numeric:
                df = df.infer_objects()
            if index is not '':
                df.index = df[index]
            return df
        except (ValueError, JSONDecodeError):
            if res.status_code == 400:
                raise r.HTTPError('400 '
                                  + '\n'.join(map(lambda x: x.decode(),
                                                  res.iter_lines())))
            else:
                res.raise_for_status()
                raise ParseException(
                    'A Valid http query passed through but failed to parse!'
                    ' For more information, inspect the `response` attribute '
                    'of this exception.',
                    response=res)

    def _bigcolq(self, cols=None, geo_unit='', geo_filter={}, apikey=None, **kwargs):
        """
        Helper function to manage large queries

        Parameters
        -----------
        cols : large list of columns to be grabbed in a query
        """
        assert (not (cols is None)), 'Columns must be provided for query!'
        if len(cols) < 50:
            print('tiny query!')
            return self.query(cols, geo_unit, geo_filter, apikey, **kwargs)
        else:
            result = pd.DataFrame()
            chunks = np.array_split(cols, math.ceil(len(cols) / 49.))
            for chunk in chunks:
                tdf = self.query(list(chunk), geo_unit,
                                 geo_filter, apikey, **kwargs)
                noreps = [x for x in tdf.columns if x not in result.columns]
                result = pd.concat([result, tdf[noreps]], axis=1)
            return result

    def varslike(self, pattern=None, by=None, engine='re', within=None):
        """
        Grabs columns that match a particular search pattern.

        Parameters
        ----------
        pattern : str
                  a search pattern to match
        by      : str
                  a column in the APIConnection.variables to conduct the search
                  within
        engine  : {'re', 'fnmatch', callable}
                  backend string matching module to use, or a function of the form
                  match(candidate, pattern). (default: 're')
        within  : pandas.DataFrame 
                  the variables over which to search.

        Notes
        ------
        Only regex and fnmatch will be supported modules. Note that, while
        regex is the default, the python regular expressions module has some
        strange behavior if you're used to VIM or Perl-like regex. It may be
        easier to use fnmatch if regex is not providing the results you expect.

        If you want, you can also pass an engine that is a function. If so, this
        needs to be a function that has a signature like:

        fn(candidate, pattern)

        and return True or False if the candidate matches the pattern. So, for
        instance, you can use any string processing function:

            >>> cxn.varslike('_100M', engine = lambda c,p: c.endswith(p)

        which may also be expressed as a regexp:

            >>> cxn.varslike('_100M$', engine='re')

        or an fnmatch pattern:

            >>> cxn.varslike('*_100M', engine='fnmatch')
        """
        if within is None:
            within = self.variables
        search_in = within.get(by, within.index).fillna('')

        if (engine == 'regex') or (engine == 're'):
            import re
            mask = [(re.search(pattern, candidate) is not None)
                        for candidate in search_in]
        elif engine == 'fnmatch':
            import fnmatch
            matches = fnmatch.filter(search_in, pattern)
            mask = search_in.isin(matches)
        elif callable(engine):
            matches = [ix for ix in search_in if engine(ix, pattern)]
            mask = search_in.isin(matches)
        else:
            raise TypeError("Engine option is not supported or not callable.")
        return within[mask]

    def set_mapservice(self, key):
        """
        Assign a mapservice to the connection instance

        Parameters
        -----------
        key : str
                string describing the shortcode of the Tiger mapservice

        Returns
        --------
        adds a mapservice attribute to the connection object, returns none.
        """
        if isinstance(key, tig.TigerConnection):
            self.mapservice = key
        elif isinstance(key, str):
            self.mapservice = tig.TigerConnection(name=key)
        return self
