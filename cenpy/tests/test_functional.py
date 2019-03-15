
# coding: utf-8

# # Grabbing data with cenpy

# Cenpy (`sen - pie`) is a package that exposes APIs from the US Census Bureau and makes it easy to pull down and work with Census data in Pandas. First, notice that there are two core modules in the package, `base` and `explorer`, which each do different things. First, let's look at `explorer`. 

# In[1]:

def test_all():
    import cenpy as c
    import pandas


    # On import, `explorer` requests all currently available APIs from the Census Bureau's [API listing](http://www.census.gov/data/developers/data-sets.html). In future, it will can also read a `JSON` collection describing the databases from disk, if asked.
    # 
    # Explorer has two functions, `available` and `explain`. `available` will provide a list of the identifiers of all the APIs that `cenpy` knows about. If run with `verbose=True`, `cenpy` will also include the title of the database as a dictionary. It's a good idea to *not* process this directly, and instead use it to explore currently available APIs.
    # 
    # Also, beware that the US Census Bureau can change the names of the resources. This means that the index of the following table is not necessarily stable over time; sometimes, the same resource can change its identifier, like when the 2010 decennial census changed from `2010sf1` to `DECENNIALSF12010`. So, consult the table built by `cenpy.explorer.available()` if the keys appear to have changed.  
    # 
    # Here, I'll just show the first five entries:

    # In[2]:


    c.explorer.available().head()


    # The `explain` command provides the title and full description of the datasource. If run in verbose mode, the function returns the full `json` listing of the API. 

    # In[3]:


    c.explorer.explain('DECENNIALSF12010')


    # To actually connect to a database resource, you create a `Connection`. A `Connection` works like a *very* simplified connection from the `sqlalchemy` world. The `Connection` class has a method, `query` that constructs a query string and requests it from the Census server. This result is then parsed into JSON and returned to the user.  

    # In[4]:


    conn = c.base.Connection('DECENNIALSF12010')


    # That may have taken longer than you'd've expected. This is because, when the `Connection` constructor is called, it populates the connection object with a bit of metadata that makes it possible to construct queries without referring to the census handbooks. 
    # 
    # For instance, a connection's `variables` represent all available search parameters for a given dataset. 

    # In[5]:


    conn.variables.head()


    # This dataframe is populated just like the census's table describing the variables on the corresponding [api website](https://api.census.gov/data/2010/dec/sf1/variables.html). Fortunately, this means that you can modify and filter this dataframe just like you can regular pandas dataframes, so working out what the exact codes to use in your query is easy. 
    # 
    # I've added a function, `varslike`, that globs variables that fit a regular expression pattern. It can use the builtin python `re` module, in addition to the `fnmatch` module. It also can use any filtering function you want. 
    # 
    # So, you can extract the rows of the variables using the `df.ix` method on the list of columns that match your expression:

    # In[6]:


    conn.variables.loc[conn.varslike('H011[AB]')]


    # Likewise, the different levels of geographic scale are determined from the metadata in the overall API listing and recorded. 
    # 
    # However, many Census products have multiple possible geographical indexing systems, like the deprecated `fips` code system and the new *Geographical Names Information System*, `gnis`. Thus, the `geographies` property is a dictionary of dataframes, where each key is the name of the identifier system and the value is the dataframe describing the identifier system. 
    # 
    # For the 2010 census, the following systems are available:

    # In[7]:


    conn.geographies.keys()


    # For an explanation of the geographic hierarchies, the `geographies` tables show the geographies at which the data is summarized:

    # In[8]:


    conn.geographies['fips'].head()


    # Note that some geographies in the `fips` system have a **requires** filter to prevent drawing too much data. This will get passed to the `query` method later. 

    # So, let's just grab the housing information from the 2010 Census Short Form. Using the variables table above, we picked out a subset of the fields we wanted. Since the variables table is indexed by the identifiers, we can grab the indexes of the filtered dataframe as query parameters. 
    # 
    # In addition, adding the `NAME` field smart-fills the table with the name of the geographic entity being pulled from the Census.

    # In[9]:


    cols = conn.varslike('H00[012]*', engine='fnmatch')


    # In[10]:


    cols.append('NAME')


    # In[11]:


    cols


    # Now the query. The query is constructed just like the API query, and works as follows. 
    # 
    # 1. cols - list of columns desired from the database, maps to census API's `get=`
    # 2. geo_unit - string denoting the unit of study to pull, maps to census API's `in=`
    # 3. geo_filter - dictionary containing groupings of geo_units, if required, maps to `for=`
    #     
    # To be specific, a fully query tells the server *what* columns to pull of *what* underlying geography from *what* aggregation units. It's structured using these heterogeneous datatypes so it's easy to change the smallest units quickly, while providing sufficient granularity to change the filters and columns as you go. 
    # 
    # This query below grabs the names, population, and housing estimates from the ACS, as well as their standard errors from census designated places in Arizona. 
    # 

    # In[12]:


    data = conn.query(cols, geo_unit = 'place:*', geo_filter = {'state':'04'})


    # Once constructed, the query executes as fast as your internet connection will move. This query has:

    # In[13]:


    data.shape


    # 28 columns and 451 rows. So, rather fast. 
    # 
    # For validity and ease of use, we store the last executed query to the object. If you're dodgy about your census API key never being shown in plaintext, never print this property!

    # In[14]:


    conn.last_query


    # So, you have a dataframe with the information requested, plus the fields specified in the `geo_filter` and `geo_unit`. Sometimes, the `pandas.infer_objects()` function is not able to infer the types or structures of the data in the ways that you might expect. Thus, you may need to format the final data to ensure that the data types are correct. 
    # 
    # So, the following is a dataframe of the data requested. I've filtered it to only look at data where the population is larger than 40 thousand people.
    # 
    # Pretty neat!

    # In[15]:


    data[data['H001001'].astype(int) > 40000]


    # And, just in case you're liable to forget your FIPS codes, the explorer module can look up some fips codes listings for you.

    # In[16]:


    c.explorer.fips_table('place', in_state='AZ')


    # ### GEO & Tiger Integration

    # The Census TIGER geometry API is substantively different from every other API, in that it's an ArcGIS REST API. But, I've tried to expose a consistent interface. It works like this:

    # In[17]:


    import cenpy.tiger as tiger


    # In[18]:


    tiger.available()


    # In some cases, it makes quite a bit of sense to "attach" a map server to your connection. In the case of the US Census 2010 we've been using, there is an obvious data product match in `tigerWMS_Census2010`. So, let's attach it to the connection.

    # In[19]:


    conn.set_mapservice('tigerWMS_Census2010')


    # In[20]:


    conn.mapservice


    # neat! this is the same as calling: 
    # 
    # `tiger.TigerConnection('tigerWMS_Census2010')`
    # 
    # but this attaches that object it to the connection you've been using. The connection also updates with this information:

    # In[21]:


    conn


    # An ESRI MapServer is a big thing, and `cenpy` doesn't support all of its features. Since `cenpy` is designed to support retreival of data from the US Census, we only support `GET` statements for defined geographic units, and ignore the vaious other functionalities in the service. 
    # 
    # To work with a service, note that any map server is composed of layers:

    # In[22]:


    conn.mapservice.layers


    # These layers are what actually implement query operations. For now, let's focus on the same "class" of units we were using before, Census Designated Places:

    # In[23]:


    conn.mapservice.layers[36]


    # A query function is implemented both at the mapservice level and the layer level. At the mapservice level, a layer ID is required in order to complete the query. 
    # 
    # Mapservice queries are driven by SQL. So, to grab all of the geodata that fits the CDPs we pulled before, you could start to construct it like this. 
    # 
    # First, just like the main connection, each layer has a set of variables: 

    # In[24]:


    conn.mapservice.layers[36].variables


    # Our prior query grabbed the places in AZ. So, we could use a SQL query that focuses on that. 
    # 
    # I try to pack the geometries into containers that people are used to using. Without knowing if GEOS is installed on a user's computer, I use `PySAL` as the target geometry type. 
    # 
    # If you do have GEOS, that means you can use Shapely or GeoPandas. So, to choose your backend, you can use the following two arguments to this query function. the `pkg` argument will let you choose the three types of python objects to output to. 
    # 
    # Pysal is default. If you select Shapely, the result will just be a pandas dataframe with Shapely geometries instead of pysal geometries. If you choose geopandas (or throw a gpize) option, cenpy will try to convert the pandas dataframe into a GeoPandas dataframe.

    # In[25]:


    geodata = conn.mapservice.query(layer=36, where='STATE = 04')


    # In[26]:


    geodata.head()


    # To join the geodata to the other data, use pandas functions:

    # In[27]:


    import pandas as pd


    # In[28]:


    newdata = pd.merge(data, geodata, left_on='place', right_on='PLACE')


    # In[29]:


    newdata.head()


    # So, that's how you get your geodata in addition to your regular data!

    # ## OK, that's one API, does it work for others?

    # We'll try the Economic Census

    # In[30]:


    conn2 = c.base.Connection('CBP2012')


    # Alright, let's look at the available columns:

    # In[31]:


    conn2.variables


    # To show the required predicates, can filter the `variables` dataframe by the `required` field. Note that *required* means that the query **will fail** if these are not passed as keyword arguments. They don't have to specify a single value, though, so they can be left as a wild card, like we did with `place:*` in the prior query:

    # In[32]:


    conn2.variables[~ conn2.variables.required.isnull()]


    # Like before, geographies are shown within a given hierarchy. Here, the only geography is the `fips` geography. 

    # In[33]:


    conn2.geographies.keys()


    # In[34]:


    conn2.geographies['fips']


    # Now, we'll do some fun with error handling and passing of additional arguments to the query. Any "extra" required predicates beyond `get`, `for` and `in` are added at the end of the query as keyword arguments. These are caught and introduced into the query following the API specifications. 
    # 
    # First, though, let's see what happens when we submit a malformed query!
    # 
    # Here, we can query for every column in the dataset applied to places in California (`fips = 06`). The dataset we're working with, the Economic Census, requires an `OPTAX` field, which identifies the "type of operation or tax status code" along which to slice the data. Just like the other arguments, we will map them to keywords in the API string, and a wildcard represents a slice of all possible values. 

    # In[35]:


    cols = conn2.varslike('ESTAB*', engine='fnmatch')


    # In[36]:


    data2 = conn2.query(cols=cols, geo_unit='county:*', geo_filter={'state':'06'})


    # In[37]:


    data2.head()


    # And so you get the table of employment by County & NAICS code for employment and establishments in California counties. Since we're using counties as our unit of analysis, we could grab the geodata for counties.

    # In[38]:


    conn2.set_mapservice('State_County')


    # But, there are quite a few layers in this MapService:

    # In[39]:


    len(conn2.mapservice.layers)


    # Oof. If you ever want to check out the web interface to see what it looks like, you can retrieve the URLs of most objects using:

    # In[40]:


    conn2.mapservice._baseurl


    # Anyway, we know counties don't really change all that much. So, let's just pick a counties layer and pull it down for California:

    # In[41]:


    geodata2= conn2.mapservice.query(layer=1,where='STATE = 06')


    # In[42]:


    newdata2 = pd.merge(data2, geodata2, left_on='county', right_on='COUNTY')


    # In[43]:


    newdata2.head()


    # And that's all there is to it! Geodata and tabular data from the Census APIs in one place.
    # 
    # [File an issue](https://github.com/ljwolf/cenpy/issues/new) if you have concerns!
