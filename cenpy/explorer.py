import requests as r
from json import JSONDecodeError
from six import iteritems as diter
import pandas as pd
import os
import six

if six.PY3:
    unicode = str

fp = os.path.dirname(os.path.realpath(__file__))

resp = raw_APIs = r.get('https://api.census.gov/data.json')
try:
    resp.raise_for_status()
    raw_APIs = resp.json()['dataset']
    APIs = {entry['identifier'].split('id')[-1].lstrip('/'): {key: value for key,
                                                              value in diter(entry) if key != entry['identifier']} for entry in raw_APIs}
except r.HTTPError:
    raise r.HTTPError('The main Census API Endpoint (https://api.census.gov/data.json) is not available.'
                      ' Try visiting https://api.census.gov/data.json in a web browser to verify connectivity.')
except JSONDecodeError:
    raise JSONDecodeError('The main Census API Endpoint (https://api.census.gov/data.json) returned malformed content.'
                          ' Try visiting https://api.census.gov/data.json in a web browser to verify connectivity.')

def available(verbose=True):
    """
    Returns available identifiers for Census Data APIs. 
    NOTE: we do not support the Economic Indicators Time Series API yet.

    Parameters
    ----------
    verbose : bool
              whether to provide ID and title or just ID (default: True)

    Returns
    --------
    
    list
        identifiers (if verbose: and dataset names)

    """
    av_apis = [api for api in APIs.keys() if 'eits' not in api]
    av_apis = [api for api in av_apis if APIs[api]
               ['distribution'][0]['format'] == 'API']
    if verbose:
        return _parse_results_table_from_response(raw_APIs).sort_index()
    else:
        return av_apis


def _parse_results_table_from_response(datajson):
    """ parse the raw data.json response into something more useful """
    raw_table = pd.DataFrame(raw_APIs)
    shortcodes = [entry['identifier'].split('id')[-1].lstrip('/')
                  for entry in raw_APIs]
    raw_table.index = shortcodes
    raw_table = raw_table[[
        col for col in raw_table.columns if not col.startswith('@')]]
    listcols = raw_table.applymap(lambda x: isinstance(x, list)).any()
    listcols = listcols.index[listcols]
    raw_table[listcols] = raw_table[listcols].apply(_delist)
    raw_table['publisher'] = raw_table['publisher'].apply(
        lambda x: x.get('name', None))
    raw_table.rename(columns=dict(identifier='identifier_url',
                                  c_vintage='vintage'), inplace=True)
    for col in raw_table:
        if isinstance(raw_table[col].iloc[0], str):
            if raw_table[col].iloc[0].startswith('http://'):
                raw_table.drop(col, axis=1, inplace=True)
    return raw_table[raw_table.columns[::-1]]


def _delist(series):
    """ turn listed cols into tuples, or extract their single element """
    series = series.copy(deep=True)
    lens = series.dropna().apply(len).unique()
    if len(lens) > 1:  # cast to tuples
        series[~series.isnull()] = series.dropna().apply(tuple)
    elif len(lens) == 1 and lens.item() == 1:  # grab single element
        series[~series.isnull()] = series.dropna().apply(lambda x: x[0])
    return series


def explain(identifier=None, verbose=False):
    """
    Explains datasets currently available via the census API

    Parameters
    ----------
    identifier : string 
                 shortcode identifying which dataset in the API to use
    verbose : bool
              flag governing whether to provide full API record
              or just title and description. (default: False)

    Returns
    --------
    dict
        title and description (if verbose: and full API information)
    """
    if identifier is None:
        raise ValueError(
            'No identifier provided. Use available() to discover identifiers')
    elif not verbose:
        return {APIs[identifier]['title']: APIs[identifier]['description']}
    else:
        return APIs[identifier]


def fips_table(kind, in_state=''):
    """
    Pulls a table of FIPS codes for reference

    Parameters
    ----------
    kind : str
           identifying the kind of census geography needed, down
           to sub-county or VTD fips
    in_state : str
                filter to only grab fips codes from within a state. Use to 
                avoid large data downloads if you're looking for specific data.
                (default: '')

    Returns
    --------

    pandas.DataFrame
        fips codes and names of the geographies in question


    """
    qurl = u'https://www2.census.gov/geo/docs/reference/codes/files/'
    tdict = {'AIA': 'aia.txt',
             'COUNTY': 'county.txt',
             'SUBCOUNTY': 'cousub.txt',
             'PLACE': 'places.txt',
             'SCHOOLDISTRICT': 'schdist.txt',
             'VTD': 'vtd.txt',
             'STATE': None}

    kind = kind.upper()
    if len(kind.split(' ')) > 1:
        kind = ''.join(kind.split(' '))

    in_state = in_state.upper()

    stfips = pd.read_csv(fp + '/stfipstable.csv')

    if kind == 'STATE':
        return stfips
    elif kind in tdict.keys():
        if in_state == '':
            qurl += 'national_' + tdict[kind]
        else:
            if in_state in stfips['State Abbreviation'].tolist():
                fips = stfips[stfips['State Abbreviation']
                              == in_state]['FIPS Code'].values[0]
            elif in_state in stfips['State Name'].tolist():
                fips = stfips[stfips['State Name'] ==
                              in_state]['FIPS Code'].values[0]
                in_state = stfips[stfips['State Name'] ==
                                  in_state]['State Abbreviation'].values[0]
            elif in_state in stfips['FIPS Code'].tolist():
                fips = in_state
                in_state = stfips[stfips['FIPS Code' == fips]
                                  ]['State Abbreviation'].values[0]
            else:
                raise KeyError('Did not find State Abbreviation or Name')
            if kind == 'COUNTY':
                qurl += 'st' + unicode(fips).rjust(2, '0') + '_' + \
                    unicode(in_state).lower() + '_' + 'cou.txt'
            else:
                qurl += 'st' + unicode(fips).rjust(2, '0') + '_' + \
                    unicode(in_state).lower() + '_' + tdict[kind]
    else:
        raise KeyError('Requested Kind not in ', tdict.keys())

    if kind in ['PLACE', 'VTD']:
        sep = '|'
        header = 0
    else:
        sep = ','
        header = None
    return pd.read_csv(qurl, sep=sep, header=header, encoding='latin1')
