from setuptools import setup, find_packages

version = '2.0.1'

setup(
    name='plone.app.upgrade',
    version=version,
    description="Upgrade machinery for Plone.",
    long_description=(open("README.rst").read() + "\n" +
                      open("CHANGES.rst").read()),
    classifiers=[
        "Environment :: Web Environment",
        "Framework :: Plone",
        "Framework :: Plone :: 4.3",
        "Framework :: Plone :: 5.0",
        "Framework :: Plone :: 5.1",
        "Framework :: Zope2",
        "License :: OSI Approved :: GNU General Public License (GPL)",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        'Programming Language :: Python :: 2.6',
        "Programming Language :: Python :: 2.7",
    ],
    keywords='Plone upgrade migration',
    author='Plone Foundation',
    author_email='plone-developers@lists.sourceforge.net',
    url='https://pypi.python.org/pypi/plone.app.upgrade',
    license='GPL version 2',
    packages=find_packages(exclude=['ez_setup']),
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
        'plone.app.folder',
        'transaction',
        'zope.component',
        'zope.interface',
        'zope.ramcache',
        'Acquisition',
        'Products.CMFPlone',
        'Products.CMFCore',
        'Products.CMFEditions',
        'Products.CMFQuickInstallerTool',
        'Products.GenericSetup>=1.8.1',
        'Products.PlonePAS',
        'Products.PluggableAuthService',
        'Products.ZCatalog >= 2.13.4',
        'Zope2',
        'plone.contentrules',
        'plone.app.iterate',
        'plone.app.viewletmanager',
    ],
    entry_points="""
    [z3c.autoinclude.plugin]
    target = plone
    """,
)
