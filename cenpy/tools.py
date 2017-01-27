import itertools as it

def state_to_block(stfips, cxn, *columns):
    """
    Casts the generator constructed by genstate_to_block to a full dataframe. 
    For arguments, see genstate_to_block
    """
    pd.concat(list(genstate_to_block(stfips, cxn, *columns)))

def state_to_blockgroup(stfips, cxn, *columns):
    """
    Casts the generator constructed by genstate_to_blockgroup to a full dataframe. 
    For arguments, see genstate_to_blockgroup
    """
    pd.concat(list(genstate_to_block(stfips, cxn, *columns)))

def state_to_tract(stfips, cxn, *columns):
    """
    Casts the generator constructed by genstate_to_tract to a full dataframe. 
    For arguments, see genstate_to_tract
    """
    pd.concat(list(genstate_to_tract(stfips, cxn, *columns)))

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

