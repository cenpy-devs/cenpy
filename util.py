import pandas as pd
import requests

API_URL="http://api.censusreporter.org/1.0/data/show/{release}?table_ids={table_ids}&geo_ids={geoids}"
def get_data(tables=None, geoids=None, release='latest'):
    if geoids is None:
        geoids = ['040|01000US']
    elif isinstance(geoids,basestring):
        geoids = [geoids]
    if tables is None:
        tables = ['B01001']
    elif isinstance(tables,basestring):
        tables=[tables]

    url = API_URL.format(table_ids=','.join(tables).upper(), 
                         geoids=','.join(geoids), 
                         release=release)
    response = requests.get(url)
    return response.json()

def get_dataframe(tables=None, geoids=None, release='latest',geo_names=False,col_names=False,include_moe=False):
    response = get_data(tables=tables,geoids=geoids,release=release)
    frame = pd.DataFrame.from_dict(prep_for_pandas(response['data'],include_moe),orient='index')
    frame = frame[sorted(frame.columns.values)] # data not returned in order
    if geo_names:
        geo = pd.DataFrame.from_dict(response['geography'],orient='index')
        frame.insert(0,'name',geo['name'])
    if col_names:
        d = {}
        for table_id in response['tables']:
            columns = response['tables'][table_id]['columns']
            for column_id in columns:
                d[column_id] = columns[column_id]['name']
        frame = frame.rename(columns=d)
    return frame

def prep_for_pandas(json_data,include_moe=False):
    """Given a dict of dicts as they come from a Census Reporter API call, set it up to be amenable to pandas.DataFrame.from_dict"""
    result = {}
    for geoid, tables in json_data.items():
        flat = {}
        for table,values in tables.items():
            for kind, columns in values.items():
                if kind == 'estimate':
                    flat.update(columns)
                elif kind == 'error' and include_moe:
                    renamed = dict((k+"_moe",v) for k,v in columns.items())
                    flat.update(renamed)
        result[geoid] = flat
    return result

if __name__ == '__main__':
    df = get_dataframe()
    print "Top 10 most populous states"
    print df.sort('B01001001',ascending=False)['B01001001'].head(10)
