from setuptools import setup
import os

basepath = os.path.dirname(__file__)
init = os.path.join(basepath, 'cenpy/__init__.py')

with open(init, 'r') as initfile:
    firstline = initfile.readline()
init_version = firstline.split('=')[-1].strip()
init_version = init_version.replace("'","")

with open(os.path.join(basepath, 'README.rst'), 'r') as readme:
    long_description = readme.readlines()
long_description = ''.join(long_description)

with open(os.path.join(basepath, 'requirements.txt'), 'r') as reqfile:
    reqs = reqfile.readlines()
reqs = [req.strip() for req in reqs]

setup(name='cenpy',
      version=init_version,
      description='Explore and download data from Census APIs',
      long_description=long_description,
      url='https://github.com/ljwolf/cenpy',
      author='Levi John Wolf',
      author_email='levi.john.wolf@gmail.com',
      license='3-Clause BSD',
      python_requires='>=3.5',
      packages=['cenpy'],
      install_requires=reqs,
      package_data={'cenpy': ['stfipstable.csv']},
      zip_safe=False)
