CenPy
=====
.. image:: https://img.shields.io/static/v1.svg?label=documentation&message=latest&color=blueviolet
    :target: https://cenpy-devs.github.io/cenpy
.. image:: https://github.com/cenpy-devs/cenpy/workflows/.github/workflows/build.yml/badge.svg
    :target: https://github.com/cenpy-devs/cenpy/actions?query=workflow%3A.github%2Fworkflows%2Fbuild.yml
.. image:: https://img.shields.io/pypi/dm/cenpy.svg
    :target: https://pypi.org/project/cenpy/
.. image:: https://zenodo.org/badge/36956226.svg
    :target: https://zenodo.org/badge/latestdoi/36956226
.. image:: https://img.shields.io/badge/Census%20Slack--lightgrey.svg
    :target: https://uscensusbureau.slack.com/messages/C8Y5PUE4D

An interface to explore and query the US Census API and return Pandas
Dataframes. This package is intended for exploratory data
analysis and draws inspiration from sqlalchemy-like interfaces and
``acs.R``. With separate APIs for application developers and folks who 
only want to get their data quickly & painlessly, ``cenpy`` should meet
the needs of most who aim to get US Census Data from Python. 

A few examples are available from `our website <https://cenpy-devs.github.io/cenpy>`__:

- `getting data quickly using Cenpy <https://nbviewer.jupyter.org/github/cenpy-devs/cenpy/blob/master/notebooks/product-api.ipynb>`__.
- `analyzing segregation over time & across space using cenpy and segregation <https://nbviewer.jupyter.org/github/cenpy-devs/cenpy/blob/master/notebooks/segregation.ipynb>`__
- `a road to frictionless urban data science using cenpy and osmnx <https://nbviewer.jupyter.org/github/cenpy-devs/cenpy/blob/master/notebooks/osmnx-and-cenpy.ipynb>`__
- `developer building blocks <http://nbviewer.ipython.org/github/cenpy-devs/cenpy/blob/master/notebooks/automatic-wrapper.ipynb>`__.
- `piecing together the developer building blocks (by @dfolch) <https://nbviewer.jupyter.org/gist/dfolch/2440ba28c2ddf5192ad7>`__

Installation
------------

Cenpy is easiest to install using ``conda``, a commonly-used package manager for scientific python. First, `install Anaconda <https://www.anaconda.com/distribution/>`__.

Then, ``cenpy`` is available on the ``conda-forge`` channel:
::

    conda install -c conda-forge cenpy

Alternatively, you can install cenpy *via* ``pip``, the python package manager, if you have installed ``geopandas`` and ``rtree``:
:: 

    pip install cenpy


For Users
----------
Most of the time, users want a simple and direct interface to the US Census Bureau's main products: the 2010 Census and the American Community Survey. Fortunately, cenpy provides a direct interface to these products. For instance, the American Community Survey's most recent 5-year estimates can be accessed using:

::

    import cenpy
    acs = cenpy.products.ACS()
    acs.from_place('Chicago, IL')

Likewise, the decennial census can be accessed using:

::

    import cenpy
    decennial = cenpy.products.Decennial2010()
    decennial.from_place('Seattle, WA')

For more information on how the product API works, consult the `notebook on the topic <https://nbviewer.jupyter.org/github/cenpy-devs/cenpy/blob/master/notebooks/product-api.ipynb>`__.


For Developers
----------------
The API reference is available at `cenpy-devs.github.io/cenpy <https://cenpy-devs.github.io/cenpy>`__. The ``products`` are typically what most end-users will want to interact with. If you want more fine-grained access to the USCB APIs, you will likely want to build on top of ``APIConnection`` and ``TigerConnection``.

At a high level, the ``APIConnection`` object connects to resources exposed on the US Census Bureau's API at ``https://api.census.gov/data.json``. Its methods and relevant utilities are defined in ``cenpy.remote``. The ``TigerConnection`` wraps one map service exposed at ``http://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb`` and is defined in ``cenpy.tiger``. Each ``TigerConnection`` is composed of many ``ESRILayer`` objects, which wrap an individual geography within the ESRI map service. For instance, an ACS ``TigerConnection`` may contain State, County, and Tract ``ESRILayer`` objects within their ``layer`` attribute. 

To use the developer-focused API, you can create an ``APIConnection`` using its shortcode:

::

    cxn = cenpy.remote.APIConnection('DECENNIALSF12010')

Check the variables required and geographies supported:

::

    cxn.variables #is a pandas dataframe containing query-able vbls
    cxn.geographies #is a pandas dataframe containing query-able geographies

Note that some geographies (like tract) have requirements higher in the hierarchy
that you'll have to specify for the query to work.

The structure of the query function maps to the Census API's use of
``get``, ``for``, and ``in``. The main arguments for the query function
are ``cols``, ``geo_unit`` and ``geo_filter``, and map back to those predicates, respectively. If more predicates are required for the
search, they can be added as keyword arguments at the end of the query.

The ``cols`` argument must be a list of columns to retrieve from the
dataset. Then, you must specify the ``geo_unit`` and ``geo_filter``,
which provide *what* the unit of aggregation should be and *where* the
units should be. ``geo_unit`` must be a string containing the unit of
analysis and an identifier. For instance, if you want all counties in
Arizona, you specify ``geo_unit = 'county:*'`` and ``geo_filter =
{'state':'04'}``.

To create a ``TigerConnection``:

::

    cxn = cenpy.tiger.TigerConnection('tigerWMS_ACS2013')

Then, all of the ``ESRILayer`` objects are contained in the ``layer`` attribute:

::

    cxn.layers

the ``cxn.query`` method passes the relevant query down to the chosen layer and returns a ``geopandas`` dataframe. The actual query is structured like ``SQL``, and follows the `ESRI documentation. <https://tigerweb.geo.census.gov/arcgis/sdk/rest/index.html#//02ss0000006v000000>`__  

Contributing
------------

To contribute to ``cenpy``:

1. Use ``cenpy``! Every user is a contributor in kind. If you feel like it, `file an issue <https://help.github.com/en/articles/github-glossary#issue>`__:

   - to tell us how you use ``cenpy``. 
   - to post a code snippit, a jupyter notebook, or whatever you can. 
   - to tell us about your `blog posts! <https://medium.com/@mswhitetoyou/scraping-us-census-data-via-cenpy-9aeab12c877e>`__
   - to ask questions about how you might use census data from Python, and we'll try to help. 

2. If you're using ``cenpy`` and something goes wrong, `file an issue <https://help.github.com/en/articles/github-glossary#issue>`__ telling us:

   - what you want that is not in ``cenpy`` or doesn't work well in other packages
   - what functionality in ``cenpy`` isn't working how you believe it ought
   - what in the documentation isn't spelled correctly or is confusing

3. `Fork <https://help.github.com/en/articles/github-glossary#fork>`__ the ``cenpy-devs/cenpy`` github repository, make changes, and send us a `pull request <https://help.github.com/en/articles/github-glossary#pull-request>`__ 

ToDo:
-----

- A product in ``cenpy.products`` for County Business Statistics
