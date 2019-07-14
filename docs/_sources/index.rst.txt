.. documentation master file

Cenpy
=====

Cenpy (pronounced sen-pie) is a package that automatically discovers US Census Bureau API endpoints and exposes them to Python in a consistent fashion. It also provides easy-to-use access to certain well-used data products, like the American Community Survey (ACS) and 2010 Decennial Census. To get started, check out one of the case studies shown below.

.. raw:: html

    <div class="container-fluid">
      <div class="row">
        <div class="col-lg-3">
            <a href="https://nbviewer.jupyter.org/github/ljwolf/cenpy/blob/product/notebooks/product-api.ipynb" class="thumbnail">
                <img src="_static/images/product.png" class="img-responsive center-block">
                <div class="caption text-center">
                <h6>Getting Data using cenpy</h6>
                </div>
            </a>
        </div>
        <div class="col-lg-3">
            <a href="https://nbviewer.jupyter.org/github/ljwolf/cenpy/blob/product/notebooks/segregation.ipynb" class="thumbnail">
                <img src="_static/images/segregation.png" class="img-responsive center-block">
                <div class="caption text-center">
                <h6>Segregation in Time and Space with cenpy and pysal</h6>
                </div>
            </a>
        </div>
        <div class="col-lg-3">
            <a href="https://nbviewer.jupyter.org/github/ljwolf/cenpy/blob/product/notebooks/osmnx-and-cenpy.ipynb" class="thumbnail">
                <img src="_static/images/osmnx.png"
                class="img-responsive center-block">
                <div class="caption text-center">
                <h6>A Road to Frictionless Urban Data Science: osmnx and cenpy
                </h6>
                </div>
            </a>
        </div>
        <div class="col-lg-3">
            <a href="http://nbviewer.ipython.org/github/ljwolf/cenpy/blob/product/notebooks/automatic-wrapper.ipynb" class="thumbnail">
                <img src="_static/images/developers.png"
                class="img-responsive center-block">
                <div class="caption text-center">
                <h6>The Underlying Architecture of cenpy
                </h6>
                </div>
            </a>
        </div>
      </div>
    </div>

Cenpy is easiest to install using ``conda``, a commonly-used package manager for scientific python. First, `install Anaconda <https://www.anaconda.com/distribution/>`__.

Then, ``cenpy`` is available on the ``conda-forge`` channel. You can install this using the `Anaconda Prompt`, or from within the Anaconda Navigator program. If you want to install the package from within the Anaconda Prompt, you can use:
::

   conda install -c conda-forge cenpy

Alternatively, you can install cenpy *via* ``pip``, the python package manager, if you have installed ``geopandas`` and ``rtree``:
:: 

    pip install cenpy

.. toctree::
   :hidden:
   :maxdepth: 4
   :caption: Contents:

   API <api>

.. _PySAL: https://github.com/pysal/pysal
