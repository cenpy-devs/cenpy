from setuptools import setup
import os

package = "cenpy"

basepath = os.path.dirname(__file__)
init = os.path.join(basepath, f"{package}/__init__.py")

with open(init, "r") as initfile:
    firstline = initfile.readline()
init_version = firstline.split("=")[-1].strip()
init_version = init_version.replace("'", "")

with open(os.path.join(basepath, "README.rst"), "r") as readme:
    long_description = readme.readlines()
long_description = "".join(long_description)

with open(os.path.join(basepath, "requirements.txt"), "r") as reqfile:
    reqs = reqfile.readlines()
reqs = [req.strip() for req in reqs]

setup(
    name=package,
    version=init_version,
    description="Explore and download data from Census APIs",
    long_description=long_description,
    url=f"https://github.com/{package}-devs/{package}",
    author="Levi John Wolf",
    author_email="levi.john.wolf@gmail.com",
    license="3-Clause BSD",
    python_requires=">=3.6",
    packages=[package],
    install_requires=reqs,
    package_data={package: ["stfipstable.csv"]},
    zip_safe=False,
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Science/Research",
        "Intended Audience :: Developers",
        "Intended Audience :: Education",
        "Topic :: Scientific/Engineering",
        "Topic :: Scientific/Engineering :: GIS",
        "License :: OSI Approved :: BSD License",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
    ],
)
