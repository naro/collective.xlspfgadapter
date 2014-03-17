# -*- coding: utf-8 -*-
import os
from setuptools import setup, find_packages


def read(*rnames):
    return open(os.path.join(os.path.dirname(__file__), *rnames)).read()

version = '1.1'

tests_require = ['zope.testing']

setup(name='collective.xlspfgadapter',
      version=version,
      description="An adapter for PloneFormGen that will save data internally and allows to export them as XLS file",
      long_description=read('README.txt'),
      # Get more strings from
      # http://pypi.python.org/pypi?%3Aaction=list_classifiers
      classifiers=[
        'Framework :: Plone',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU General Public License (GPL)',
        ],
      keywords='',
      author='',
      author_email='',
      url='http://svn.plone.org/svn/collective/',
      license='GPL',
      packages=find_packages(exclude=['ez_setup']),
      namespace_packages=['collective', ],
      include_package_data=True,
      zip_safe=False,
      install_requires=['setuptools',
                        'Products.PloneFormGen',
                        'xlwt',
                        ],
      tests_require=tests_require,
      extras_require=dict(tests=tests_require),
      test_suite='collective.xlspfgadapter.tests.test_docs.test_suite',
      entry_points="""
      # -*- entry_points -*-
      [z3c.autoinclude.plugin]
      target = plone
      """,
      )
