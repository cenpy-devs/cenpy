import itertools as it

def state_to_block(stfips, cxn, *columns):
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


def state_to_blockgroup(stfips, cxn, *columns):
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

def state_to_tract(stfips, cxn, *columns):
    counties = cxn.query(['NAME'], geo_unit='county', geo_filter={'state':stfips})
    counties = counties.county.tolist()
    for county in counties:
        tract = cxn.query(['NAME'] + list(columns), geo_unit='tract', 
                           geo_filter={'state':stfips, 
                                       'county':county})
        yield tract

