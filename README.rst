CenPy
=====
.. image:: https://img.shields.io/static/v1.svg?label=documentation&message=latest&color=blueviolet
    :target: https://cenpy-devs.github.io/cenpy
.. image:: https://travis-ci.org/cenpy-devs/cenpy.svg?branch=master
    :target: https://travis-ci.org/cenpy-devs/cenpy
.. image:: https://img.shields.io/pypi/dm/cenpy.svg
    :target: https://pypi.org/project/cenpy/
.. image:: https://zenodo.org/badge/36956226.svg
    :target: https://zenodo.org/badge/latestdoi/36956226

An interface to explore and query the US Census API and return Pandas
Dataframes. This package is intended for exploratory data
analysis and draws inspiration from sqlalchemy-like interfaces and
``acs.R``. With separate APIs for application developers and folks who 
only want to get their data quickly & painlessly, ``cenpy`` should meet
the needs of most who aim to get US Census Data from Python. 

A few examples are available from `our website <https://cenpy-devs.github.io/cenpy>`__:

- `getting data quickly using Cenpy <https://nbviewer.jupyter.org/github/cenpy-devs/cenpy/blob/product/notebooks/product-api.ipynb>`__.
- `analyzing segregation over time & across space using cenpy and segregation <https://nbviewer.jupyter.org/github/cenpy-devs/cenpy/blob/product/notebooks/segregation.ipynb>`__
- `a road to frictionless urban data science using cenpy and osmnx <https://nbviewer.jupyter.org/github/cenpy-devs/cenpy/blob/product/notebooks/osmnx-and-cenpy.ipynb>`__
- `developer building blocks <http://nbviewer.ipython.org/github/cenpy-devs/cenpy/blob/product/notebooks/automatic-wrapper.ipynb>`__.
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

For more information on how the product API works, consult the `notebook on the topic <https://nbviewer.jupyter.org/github/cenpy-devs/cenpy/blob/product/notebooks/product-api.ipynb>`__.


For Developers
----------------
The API reference is available at `cenpy-devs.github.io/cenpy <https://cenpy-devs.github.io/cenpy>`__. The ``products`` are typically what most end-users will want to interact with. If you want more fine-grained access to the USCB APIs, you will likely want to build on top of ``APIConnection`` and ``TigerConnection``. 

To create a connection:

::

    cxn = cenpy.remote.APIConnection('DECENNIALSF12010')

Check the variables required and geographies supported:

::

    cxn.variables #is a pandas dataframe containing query-able vbls
    cxn.geographies #is a pandas dataframe containing query-able geographies

Note that some geographies (like tract) have higher-level requirements
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

ToDo:
-----

- A product in ``cenpy.products`` for County Business Statistics
