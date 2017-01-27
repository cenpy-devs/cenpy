import itertools as it
import pandas as pd
import os

def state_to_block(stfips, cxn, *columns):
    """
    Casts the generator constructed by genstate_to_block to a full dataframe. 
    For arguments, see genstate_to_block
    """
    return pd.concat(list(genstate_to_block(stfips, cxn, *columns)))

def state_to_blockgroup(stfips, cxn, *columns):
    """
    Casts the generator constructed by genstate_to_blockgroup to a full dataframe. 
    For arguments, see genstate_to_blockgroup
    """
    return pd.concat(list(genstate_to_block(stfips, cxn, *columns)))

def state_to_tract(stfips, cxn, *columns):
    """
    Casts the generator constructed by genstate_to_tract to a full dataframe. 
    For arguments, see genstate_to_tract
    """
    return pd.concat(list(genstate_to_tract(stfips, cxn, *columns)))

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
