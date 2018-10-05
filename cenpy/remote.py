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


class APIConnection():
    def __init__(self, api_name=None, apikey=''):
        """
        Constructor for a Connection object

        Parameters
        ============
        api_name : shortcode identifying which api to connect to

        Returns
        ========

        a Cenpy Connection object
        """
        if 'eits' not in api_name and api_name is not None:
            curr = exp.APIs[api_name]
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
                self.variables = v.from_dict(
                    r.get(self.__urls__['variables']).json()['variables']).T
            if 'geography' in self.__urls__.keys():
                res = r.get(self.__urls__['geography']).json()
                self.geographies = {k: pd.DataFrame().from_dict(v) for k, v
                                    in iteritems(res)}
            if 'tags' in self.__urls__.keys():
                self.tags = list(
                    r.get(self.__urls__['tags']).json().values())[0]

            if 'examples' in self.__urls__.keys():
                self.example_entries = r.get(self.__urls__['examples']).json()

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

    def explain(self, *args, **kwargs):
        """
        Explain a column or list of columns.

        Parameters
        ============
        *args : list of names of columns in the variables dataframe that require
                explanation"
        verbose : boolean denoting whether to grab both "label" and "concept"
                from the variable dataframe.

        Returns
        ==========
        dictionary of explanatory texts about variables inputted.
        """
        verbose = kwargs.pop('verbose', True)
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
        ===========
        cols : census field identifiers to pull
        geo_unit : dict or string identifying what the basic spatial
                    unit of the query should be
        geo_filter : dict of required geometries above the specified
                      geo_unit needed to complete the query
        apikey : USCB-issued key for your query.
        **kwargs : additional search predicates can be passed here

        Returns
        ========
        pandas dataframe of results

        Example
        ========
        To grab the total population of all of the census blocks in a part of Arizona:

            >>> cxn.query('P0010001', geo_unit = 'block:*', geo_filter = {'state':'04','county':'019','tract':'001802'})

        Notes
        ======

        If your list of columns exceeds the maximum query length of 50,
        the query will be broken up and concatenates back together at
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
        res.raise_for_status()
        if res.status_code == 204:
            raise r.HTTPError(str(res.status_code) +
                              ' error: no records matched your query')
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
                raise r.HTTPError(str(res.status_code) + ' ' +
                                  [l for l in res.iter_lines()][0])
            else:
                raise Exception(
                    'A Valid http query passed through but failed to parse!')
                res.raise_for_status()

    def _bigcolq(self, cols=None, geo_unit='', geo_filter={}, apikey=None, **kwargs):
        """
        Helper function to manage large queries

        Parameters
        ===========
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

    def varslike(self, pattern, engine='regex'):
        """
        Grabs columns that match a particular search pattern.

        Parameters
        ==========
        pattern : string containing a search pattern
        engine  : string describing backend string matching module to use.

        Notes
        ======
        Only regex and fnmatch will be supported modules. Note that, while
        regex is the default, the python regular expressions module has some
        strange behavior if you're used to VIM or Perl-like regex. It may be
        easier to use fnmatch if regex is not providing the results you expect.

        If you want, you can also pass an engine that is a function. If so, this
        needs to be a function that has a signature like:

        fn(candidate, pattern)

        and return True or False if the candidate matches the pattern. So, for
        instance, you can use any string processing function:

            >>> cxn.colslike('_100M', engine = lambda c,p: c.endswith(p)

        which may also be expressed as a regexp:

            >>> cxn.colslike('_100M$', engine='re')

        or an fnmatch pattern:

            >>> cxn.colslike('*_100M', engine='fnmatch')
        """

        if engine == 'regex':
            import re
            search = re.compile(pattern)
            return [candidate for candidate in self.variables.index
                    if re.match(pattern, candidate)]
        elif engine == 're':
            self.colslike(pattern, engine='regexp')
        elif engine == 'fnmatch':
            import fnmatch
            return fnmatch.filter(self.variables.index, pattern)
        elif callable(engine):
            return [ix for ix in self.variables.index if engine(ix, pattern)]
        else:
            raise TypeError("Engine option is not supported or not callable.")

    def set_mapservice(self, key):
        """
        Assign a mapservice to the connection instance

        Parameters
        ===========
        key : str
                string describing the shortcode of the Tiger mapservice

        Returns
        ========
        adds a mapservice attribute to the connection object, returns none.
        """
        if isinstance(key, tig.TigerConnection):
            self.mapservice = key
        elif isinstance(key, str):
            self.mapservice = tig.TigerConnection(name=key)
