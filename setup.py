from setuptools import setup
import os

basepath = os.path.dirname(__file__)
init = os.path.join(basepath, 'cenpy/__init__.py')

with open(init, 'r') as initfile:
    firstline = initfile.readline()
init_version = firstline.split('=')[-1].strip()
setup(name='cenpy',
      version='0.9.9',
      description='Explore and download data from Census APIs',
      url='https://github.com/ljwolf/cenpy',
      author='Levi John Wolf',
      author_email='levi.john.wolf@gmail.com',
      license='3-Clause BSD',
      python_requires='>=3.5',
      packages=['cenpy'],
      install_requires=['pandas', 'requests', 'libpysal'],
      package_data={'cenpy': ['stfipstable.csv']},
      zip_safe=False)
