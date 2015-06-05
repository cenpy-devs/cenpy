import requests as r

raw_APIs = r.get('http://api.census.gov/data.json').json()

APIs = {entry['identifier']: {key: value for key, value in entry.iteritems() if key != entry['identifier']} for entry in raw_APIs}

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
        raise ValueError('No identifier provided. Use census_pandas.available() to discover identifiers')
    elif not verbose:
        return APIs[identifier]['title'], APIs[identifier]['description']
    else:
        APIs[identifier]

