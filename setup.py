from setuptools import find_packages
from setuptools import setup


version = '2.0.32'

setup(
    name='plone.app.upgrade',
    version=version,
    description="Upgrade machinery for Plone.",
    long_description=(open("README.rst").read() + "\n" +
                      open("CHANGES.rst").read()),
    classifiers=[
        "Development Status :: 6 - Mature",
        "Environment :: Web Environment",
        "Framework :: Plone",
        "Framework :: Plone :: 5.0",
        "Framework :: Plone :: 5.1",
        "Framework :: Plone :: 5.2",
        "Framework :: Plone :: Core",
        "Framework :: Zope2",
        "Framework :: Zope :: 4",
        "License :: OSI Approved :: GNU General Public License v2 (GPLv2)",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
    ],
    keywords='Plone upgrade migration',
    author='Plone Foundation',
    author_email='plone-developers@lists.sourceforge.net',
    url='https://pypi.org/project/plone.app.upgrade/',
    license='GPL version 2',
    packages=find_packages(),
    namespace_packages=['plone', 'plone.app'],
    include_package_data=True,
    zip_safe=False,
    extras_require=dict(
        test=[
            'zope.site',
            'mock',
            'plone.app.caching',
            'plone.app.testing',
            'plone.app.theming',
        ]
    ),
    install_requires=[
        'setuptools',
        'plone.portlets',
        'transaction',
        'zope.component',
        'zope.interface',
        'zope.ramcache',
        'Acquisition',
        'Products.CMFPlone',
        'Products.CMFCore',
        'Products.CMFEditions',
        'Products.GenericSetup>=1.8.1',
        'Products.PlonePAS >= 5.0.1',
        'Products.PluggableAuthService',
        'Products.ZCatalog >= 2.13.4',
        'Zope2',
        'plone.contentrules',
        'plone.app.iterate',
        'plone.app.viewletmanager',
        'six',
    ],
    entry_points="""
    [z3c.autoinclude.plugin]
    target = plone
    """,
)
