import requests as r
from six import iteritems as diter
import pandas as pd
import os
import six

if six.PY3:
    unicode = str

fp  = os.path.dirname(os.path.realpath(__file__))

raw_APIs = r.get('http://api.census.gov/data.json').json()['dataset']

APIs = {entry['identifier'].split('id')[-1].lstrip('/'): {key: value for key,value in diter(entry) if key != entry['identifier']} for entry in raw_APIs}

def available(verbose=False):
    """
    Returns available identifiers for Census Data APIs. 
    NOTE: we do not support the Economic Indicators Time Series API yet.

    Arguments
    ==========
    verbose : boolean governing whether to provide ID and title
              or just ID

    Returns
    ========

    identifiers (if verbose: and dataset names)

    """
    av_apis = [api for api in APIs.keys() if 'eits' not in api]
    av_apis = [api for api in av_apis if APIs[api]['distribution'][0]['format'] == 'API']
    if verbose:
        return {idx: APIs[idx]['title'] for idx in av_apis}
    else:
        return av_apis

def explain(identifier=None, verbose=False):
    """
    Explains datasets currently available via the census API

    Arguments
    ==========
    identifier : string identifying which dataset in the API to use
    verbose : boolean governing whether to provide full API record
              or just title and description.

    Returns
    ========

    title and description (if verbose: and full API information)
    """
    if identifier is None:
        raise ValueError('No identifier provided. Use available() to discover identifiers')
    elif not verbose:
        return {APIs[identifier]['title']: APIs[identifier]['description']}
    else:
        return APIs[identifier]


def fips_table(kind, in_state = ''):
    """
    Pulls a table of FIPS codes for reference

    Arguments
    ==========
    kind : string identifying the kind of census geography needed, down
            to sub-county or VTD fips
    in_state : filter to only grab fips codes from within a state. Use to 
            avoid large data downloads if you're looking for specific data

    Returns
    ========

    Pandas dataframe of fips codes and names of the geographies in question


    """
    qurl = u'http://www2.census.gov/geo/docs/reference/codes/files/'
    tdict = {'AIA':'aia.txt',
            'COUNTY':'county.txt',
            'SUBCOUNTY':'cousub.txt',
            'PLACE':'places.txt',
            'SCHOOLDISTRICT':'schdist.txt',
            'VTD':'vtd.txt'}
    
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
                fips = stfips[stfips['State Abbreviation'] == in_state]['FIPS Code'].values[0]
            elif in_state in stfips['State Name'].tolist():
                fips = stfips[stfips['State Name'] == in_state]['FIPS Code'].values[0]
                in_state = stfips[stfips['State Name'] == in_state]['State Abbreviation'].values[0]
            elif in_state in stfips['FIPS Code'].tolist():
                fips = in_state
                in_state = stfips[stfips['FIPS Code' == fips]]['State Abbreviation'].values[0]
            else:
                raise KeyError('Did not find State Abbreviation or Name')
            if kind == 'COUNTY':
                qurl += 'st' + unicode(fips).rjust(2, '0') + '_' + unicode(in_state).lower() + '_' + 'cou.txt'
            else:
                qurl += 'st' + unicode(fips).rjust(2, '0') + '_' + unicode(in_state).lower() + '_' + tdict[kind]
    else:
        raise KeyError('Requested Kind not in ', tdict.keys())

    print('reading {}'.format(qurl))
    if kind in ['PLACE', 'VTD']:
       return pd.read_table(qurl, sep='|', header=None)
    else:
       return pd.read_csv(qurl, header=None)
