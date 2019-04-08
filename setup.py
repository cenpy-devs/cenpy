from setuptools import setup
import os

basepath = os.path.dirname(__file__)
init = os.path.join(basepath, 'cenpy/__init__.py')

with open(init, 'r') as initfile:
    firstline = initfile.readline()
init_version = firstline.split('=')[-1].strip()

with open(os.path.join(basepath, 'README.rst'), 'r') as readme:
    long_description = readme.readlines()
long_description = ''.join(long_description)

setup(name='cenpy',
      version='1.0.0rc2',
      description='Explore and download data from Census APIs',
      long_description=long_description,
      url='https://github.com/ljwolf/cenpy',
      author='Levi John Wolf',
      author_email='levi.john.wolf@gmail.com',
      license='3-Clause BSD',
      python_requires='>=3.5',
      packages=['cenpy'],
      install_requires=['pandas', 'requests',
                        'libpysal', 'geopandas',
                        'fuzzywuzzy'],
      package_data={'cenpy': ['stfipstable.csv']},
      zip_safe=False)
