#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""The setup script."""

from setuptools import setup, find_packages

with open("README.rst") as readme_file:
    readme = readme_file.read()

setup(
    author="Sebastian Haase",
    author_email="haase@msg.ucsf.edu",
    classifiers=[
        "Intended Audience :: Developers",
        "License :: OSI Approved :: BSD License",
        "Natural Language :: English",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
    ],
    description="Read and write .mrc and .dv (deltavision) image file format",
    install_requires=["numpy"],
    license="BSD license",
    long_description=readme,
    include_package_data=True,
    keywords="mrc",
    name="mrc",
    packages=find_packages(include=["mrc"]),
    test_suite="tests",
    url="https://github.com/tlambert03/mrc",
    version='0.1.5',
    zip_safe=False,
)
