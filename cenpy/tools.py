import itertools as it
import pandas as pd
import os
import warnings as warn
import time
from .explorer import fips_table as _ft
from requests import HTTPError
_state_fipscodes = _ft('state')['FIPS Code']
_state_fipscodes = [str(f).rjust(2, '0') for f in _state_fipscodes if f < 60] 

def national_to_block(cxn, *columns, wait_by_state=0, 
                                     wait_by_county=0):
    """
    A helper function to grab all blocks by iterating over state fips codes in cenpy.explorer.fips_table. 
    This just naively calls state_to_block for each state, so will end up executing quite a few queries. 
    You may be rate limited if you don't use an APIKEY
    Arguments
    ---------
    cxn     :   cenpy.base.Connection object
                    the connection to use to query.
    columns :   comma separated collection
                    splatted comma separated collection of column names
                    to grab from the connection. A call may be like:
                    >>> tools.national_to_block(cxn, *cxn.varslike('H001*"))
    wait_by_state : callable or int
                    if an integer, gives the number of seconds passed 
                    to sys.sleep between each state query. if callable,
                    will be called each state to get a sleep time. This
                    means you can use random waittimes. So, to wait
                    for an exponentially-distributed number of seconds:
                    >>> import random
                    >>> tools.national_to_block(cxn, 
                                                *cxn.varslike("P001*"), 
                                                wait_by_state = lambda : (random.expovariate(2) * 20))
    wait_by_county: callable or int
                    wait time (or wait time callable) applied between each county-level query. See wait_by_state for more information. If this value tends to be large, the time it takes to conduct the query can get large quickly. 
    """
    if isinstance(wait_by_state, (int, float)):
        waitfunc = lambda : wait_by_state
    else:
        waitfunc = wait_by_state
    outs = []
    for fp in _state_fipscodes:
        try:
            outs.append(state_to_block(fp, cxn, *columns, 
                                       wait=wait_by_county))
        except HTTPError:
            warn.warn('Something failed in state {}, terminating prematurely'.format(fp))
            raise
        time.sleep(waitfunc())
    return pd.concat(outs)

def national_to_tract(cxn, *columns, wait_by_state = 0,
                                     wait_by_county = 0):
    """
    A helper function to grab all tracts by iterating over state fips codes in cenpy.explorer.fips_table. 
    This just naively calls state_to_tract for each state, so will end up executing quite a few queries. 
    You may be rate limited if you don't use an APIKEY
    """
    if isinstance(wait_by_state, (int, float)):
        waitfunc = lambda : wait_by_state
    else:
        waitfunc = wait_by_state
    outs = []
    for fp in _state_fipscodes:
        try:
            outs.append(state_to_tract(fp, cxn, *columns, 
                                       wait=wait_by_county))
        except HTTPError:
            warn.warn('Something failed in state {}, terminating prematurely'.format(fp))
            raise
        time.sleep(waitfunc())
    return pd.concat(outs)

def national_to_blockgroup(cxn, *columns, wait_by_state=0, wait_by_county=0):
    """
    A helper function to grab all blockgroups by iterating over state fips codes in cenpy.explorer.fips_table. 
    This just naively calls state_to_blockgroup for each state, so will end up executing quite a few queries. 
    You may be rate limited if you don't use an APIKEY
    """
    if isinstance(wait_by_state, (int, float)):
        wait_by_state = lambda : wait_by_state
    else:
        waitfunc = wait_by_state
    outs = []
    for fp in _state_fipscodes:
        try:
            outs.append(state_to_blockgroup(fp, cxn, *columns, wait=wait_by_county))
        except HTTPError:
            warn.warn('Something failed in state {}, terminating prematurely'.format(fp))
            raise
        time.sleep(waitfunc(a))
    return pd.concat(outs)

def state_to_block(stfips, cxn, *columns, wait=0):
    """
    Casts the generator constructed by genstate_to_block to a full dataframe. 
    For arguments, see genstate_to_block
    """
    if isinstance(wait, (int, float)):
        waitfunc = lambda : wait
    else:
        waitfunc = wait
    out = []
    for cblock in genstate_to_block(stfips, cxn, *columns):
        out.append(cblock)
        time.sleep(waitfunc())
    return pd.concat(out)

def state_to_blockgroup(stfips, cxn, *columns, wait=0):
    """
    Casts the generator constructed by genstate_to_blockgroup to a full dataframe. 
    For arguments, see genstate_to_blockgroup
    """
    if isinstance(wait, (int, float)):
        waitfunc = lambda : wait
    else:
        waitfunc = wait
    out = []
    for cblock in genstate_to_blockgroup(stfips, cxn, *columns):
        out.append(cblock)
        time.sleep(waitfunc())
    return pd.concat(out)

def state_to_tract(stfips, cxn, *columns, wait=0):
    """
    Casts the generator constructed by genstate_to_tract to a full dataframe. 
    Arguments
    ---------
    stfips  :   string
                two-digit state fips code used to grab tracts
    cxn     :   cenpy.base.Connection
                connection object against which the query occurs
    *columns:   comma separated collection
                splatted list of columns to use in the query:
                >>> state_to_tract('06', cxn, 'H0010001', 'P001002')
                >>> #is equivalent to:
                >>> state_to_tract('06', cxn, *['H0010001', 'P001002'])
    wait    :   int or callable
                a number of seconds to wait before the next county
                is queried. Must be an integer or a function that 
                takes no arguments and returns a number of seconds 
                to wait. 
                
    For arguments, see genstate_to_tract
    """
    if isinstance(wait, (int, float)):
        waitfunc = lambda : wait
    else:
        waitfunc = wait
    out = []
    for cblock in genstate_to_tract(stfips, cxn, *columns):
        out.append(cblock)
        time.sleep(waitfunc())
    return pd.concat(out)

def genstate_to_block(stfips, cxn, *columns):
    """
    Generator to handle geo-in-geo queries without the user having to worry about wrangling the counties. 

    Arguments
    ----------
    stfips  :   string
                fips of the state 
    cxn     :   cenpy.base.Connection
                connection instance
    *columns:   strings
                columns that are desired by the user to grab for each block. 
    Returns
    -------
    a Generator that yields dataframes.
    """
    counties = cxn.query(['NAME'], geo_unit='county', geo_filter={'state':stfips})
    counties = counties.county.tolist()
    ctracts = ((county, tract) for county in counties 
                for tract in cxn.query(['NAME'], geo_unit='tract', 
                                       geo_filter={'state':stfips, 'county':county}).tract)
    for county,tract in ctracts:
        blocks = cxn.query(['NAME'] + list(columns), geo_unit='block', 
                           geo_filter={'state':stfips, 
                                       'county':county,
                                       'tract':tract})
        yield blocks

def genstate_to_blockgroup(stfips, cxn, *columns):
    """
    Generator to handle geo-in-geo queries without the user having to worry about wrangling the counties. 

    Arguments
    ----------
    stfips  :   string
                fips of the state 
    cxn     :   cenpy.base.Connection
                connection instance
    *columns:   strings
                columns that are desired by the user to grab for each blockgroup. 
    Returns
    -------
    a Generator that yields dataframes.
    """
    counties = cxn.query(['NAME'], geo_unit='county', geo_filter={'state':stfips})
    counties = counties.county.tolist()
    ctracts = ((county, tract) for county in counties 
                for tract in cxn.query(['NAME'], geo_unit='tract', 
                                       geo_filter={'state':stfips, 'county':county}).tract)
    for county,tract in ctracts:
        blockgroups = cxn.query(['NAME'] + list(columns), geo_unit='blockgroup', 
                           geo_filter={'state':stfips, 
                                       'county':county,
                                       'tract':tract})
        yield blockgroups

def genstate_to_tract(stfips, cxn, *columns):
    """
    Generator to handle geo-in-geo queries without the user having to worry about wrangling the counties. 

    Arguments
    ----------
    stfips  :   string
                fips of the state 
    cxn     :   cenpy.base.Connection
                connection instance
    *columns:   strings
                columns that are desired by the user to grab for each tract. 
    Returns
    -------
    a Generator that yields dataframes.
    """
    counties = cxn.query(['NAME'], geo_unit='county', geo_filter={'state':stfips})
    counties = counties.county.tolist()
    for county in counties:
        tract = cxn.query(['NAME'] + list(columns), geo_unit='tract', 
                           geo_filter={'state':stfips, 
                                       'county':county})
        yield tract

def set_sitekey(sitekey, overwrite=False):
    """
    Save the sitekey so that users can access it via cenpy.SITEKEY. 
    This lets users bind an API key to a given installation. 

    Arguments
    -----------
    sitekey     :   string
                    string containing the census data api key the user wants to bind
    overwrite   :   bool
                    flag denoting whether to overwrite existing sitekey. Defaults to False. 

    Returns
    --------
    path to the location of the sitekey file or raises FileError if overwriting is prohibited and the file exists.  
    """
    thispath = os.path.dirname(os.path.abspath(__file__))
    targetpath = os.path.join(thispath, 'SITEKEY.txt')
    if os.path.isfile(targetpath):
        if not overwrite:
            raise FileError('SITEKEY already bound and overwrite flag is not set')
    with open(targetpath, 'w') as outfile:
        outfile.write(sitekey)
    return targetpath

def _load_sitekey():
    basepath = os.path.dirname(os.path.abspath(__file__))
    targetpath = os.path.join(basepath, 'SITEKEY.txt')
    try:
        with open(targetpath, 'r') as f:
            s = f.read()
        return s.strip()
    except FileNotFoundError:
        return None
