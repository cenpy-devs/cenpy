.. _api_ref:

.. currentmodule:: cenpy 

API reference
=============

.. _cenpy_api:

Exploration Tools
------------------

These are functions that assist in understanding the census bureau products.

.. autosummary::
    :toctree: generated/


        cenpy.explorer.available
        cenpy.explorer.explain
        cenpy.explorer.fips_table

Configuration Tools
--------------------

These are functions that allow users to register their US Census Bureau API Key with ``cenpy``. 

.. autosummary::
    :toctree: generated/


        cenpy.set_sitekey

Product: American Community Survey
------------------------------------

A product that integrates the data & geographic APIs for the 5-year 2013-2017 ACSs.

.. autosummary::
    :toctree: generated/
    :nosignatures:


        cenpy.products.ACS
        cenpy.products.ACS.variables
        cenpy.products.ACS.tables
        cenpy.products.ACS.crosstab_tables
        cenpy.products.ACS.filter_variables
        cenpy.products.ACS.filter_tables
        cenpy.products.ACS.check_match
        cenpy.products.ACS.from_place
        cenpy.products.ACS.from_msa
        cenpy.products.ACS.from_csa
        cenpy.products.ACS.from_county
        cenpy.products.ACS.from_state

Product: Decennial 2010 Census
--------------------------------

A product that integrates the data & geographic APIs for the 2010 Census.

.. autosummary::
    :toctree: generated/
    :nosignatures:


        cenpy.products.Decennial2010
        cenpy.products.Decennial2010.variables
        cenpy.products.Decennial2010.tables
        cenpy.products.Decennial2010.crosstab_tables
        cenpy.products.Decennial2010.filter_variables
        cenpy.products.Decennial2010.filter_tables
        cenpy.products.Decennial2010.check_match
        cenpy.products.Decennial2010.from_place
        cenpy.products.Decennial2010.from_msa
        cenpy.products.Decennial2010.from_csa
        cenpy.products.Decennial2010.from_county
        cenpy.products.Decennial2010.from_state

Architectural Component: APIConnection
---------------------------------------

The fundamental building block that manages connections to the raw data API, a REST-ful plaintext API.

.. autosummary::
    :toctree: generated/
    :nosignatures:


        cenpy.remote.APIConnection
        cenpy.remote.APIConnection.explain
        cenpy.remote.APIConnection.query
        cenpy.remote.APIConnection.varslike
        cenpy.remote.APIConnection.set_mapservice


Architectural Component: TigerConnection
-----------------------------------------

The fundamental building block that manages connections to the geographic API, the US Census's ESRI MapService.

.. autosummary::
    :toctree: generated/
    :nosignatures:


        cenpy.tiger.TigerConnection
        cenpy.tiger.TigerConnection.query


Architectural Component: ESRILayer
--------------------------------------

The fundamental building block that manages connections to individual ESRI Layers within the ESRI MapService

.. autosummary::
    :toctree: generated/
    :nosignatures:


        cenpy.tiger.ESRILayer
        cenpy.tiger.ESRILayer.query


Architectural Component: APIConnection
---------------------------------------

The fundamental building block that provides an absract base class for subclasses, which are Census Data Products that unite raw data & geographical APIs. 

.. autosummary::
    :toctree: generated/
    :nosignatures:


        cenpy.products._Product
        cenpy.products._Product.variables
        cenpy.products._Product.tables
        cenpy.products._Product.filter_variables
        cenpy.products._Product.filter_tables
        cenpy.products._Product.from_place
        cenpy.products._Product._from_bbox
        cenpy.products._Product._from_name
        cenpy.products._Product.check_match
