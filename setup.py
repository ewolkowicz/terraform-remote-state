#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup, Command, find_packages

long_description = """
Manages Terraform Remote State with AWS S3 and some management features for applications and versioning
"""

setup(
    name = 'tfr',
    packages = find_packages(),
    version = '1.0.0',
    license='MIT',
    description = long_description,
    long_description=long_description,
    author = 'Ethan Wolkowicz, Brandon Wagner',
    author_email = 'brandon@brandonwagner.info',
    url = 'https://github.com/ewolkowicz/terraform-remote-state',
    download_url = 'https://github.com/ewolkowicz/terraform-remote-state/archive/1.0.0.tar.gz',
    scripts = ['tfr'],
    keywords = ['Terraform', 'S3', 'HashiCorp'],
    zip_safe = True,
    install_requires=['boto3']
)
