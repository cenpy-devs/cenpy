# # Downloading and Plotting U.S. Census Bureau Data Using Python
# David C. Folch | Florida State University | github: @dfolch
# 
# Rebecca Davies | University of Colorado Boulder | github: @beckymasond

import pandas as pd
import cenpy as cen


databases = [(k,v) for k,v in cen.explorer.available(verbose=True).items()]
print('total number of databases:', len(databases))
databases[0:5]

api_database = 'ACSSF5Y2012'  # ACS 2008-2012


cen.explorer.explain(api_database)

api_conn = cen.base.Connection(api_database)

queries = []
g_unit = 'state'
g_filter = {}
queries.append((g_unit, g_filter))
### select Florida
g_unit = 'state:12'
g_filter = {}
queries.append((g_unit, g_filter))
### select all counties in Florida
g_unit = 'county'
g_filter = {'state':'12'}
### select all census tracts in Florida
g_unit = 'tract'
queries.append((g_unit, g_filter))
g_filter = {'state':'12'}
### select all tracts in Leon County, Florida
g_unit = 'tract'
g_filter = {'state':'12', 'county':'073'}
queries.append((g_unit, g_filter))

cols = api_conn.varslike('B17006_\S+')
cols.extend(api_conn.varslike('B19326_\S+'))

cols_detail = pd.DataFrame(api_conn.variables.loc[cols].label)
cols_detail.head()

cols.extend(['NAME', 'GEOID'])

for query in queries:
    geo_unit, geo_filter = query
    data = api_conn.query(cols, geo_unit=g_unit, geo_filter=g_filter)
    print(data.head())
    data.index = data.GEOID
    data.index = data.index.str.replace('14000US','')
    data[['B17006_012E','B17006_012M']].head(10)


cen.tiger.available()
api_conn.set_mapservice('tigerWMS_ACS2013')
api_conn


# The ACS produces estimates from many different geographies.

# In[25]:

api_conn.mapservice.layers


api_conn.mapservice.layers[8]

### select Florida
#geodata = api_conn.mapservice.query(layer=82, where='STATE=12', pkg='geopandas')
#### select all counties in Florida
#geodata = api_conn.mapservice.query(layer=84, where='STATE=12')
#### select all census tracts in Florida
#geodata = api_conn.mapservice.query(layer=8, where='STATE=12', pkg='geopandas')
### select all tracts in Leon County, Florida
geodata = api_conn.mapservice.query(layer=8, where='STATE=12 and COUNTY=073')

newdata = pd.merge(data, geodata, left_index=True, right_on='GEOID')
