from setuptools import find_packages
from setuptools import setup

version = '1.4.7'

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
        "Framework :: Plone :: 4.3",
        "Framework :: Zope2",
        "License :: OSI Approved :: GNU General Public License v2 (GPLv2)",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        'Programming Language :: Python :: 2.6',
        "Programming Language :: Python :: 2.7",
    ],
    keywords='Plone upgrade migration',
    author='Plone Foundation',
    author_email='plone-developers@lists.sourceforge.net',
    url='https://pypi.org/project/plone.app.upgrade',
    license='GPL version 2',
    packages=find_packages(),
    namespace_packages=['plone', 'plone.app'],
    include_package_data=True,
    zip_safe=False,
    extras_require=dict(
        test=[
            'mock',
            'Products.CMFPlacefulWorkflow',
            'Products.CMFQuickInstallerTool',
            'plone.contentrules',
            'plone.app.i18n',
            'plone.app.iterate',
            'plone.app.openid',
            'plone.app.redirector',
            'plone.app.viewletmanager',
            'plone.app.testing',
            'plone.app.theming',
        ]
    ),
    install_requires=[
        'setuptools',
        'borg.localrole',
        'five.localsitemanager',
        'plone.portlets',
        'plone.session',
        'plone.app.folder',
        'plone.app.portlets',
        'transaction',
        'zope.component',
        'zope.interface',
        'zope.location',
        'zope.ramcache',
        'zope.site',
        'Acquisition',
        'Products.CMFPlone',
        'Products.Archetypes',
        'Products.contentmigration',
        'Products.CMFCore',
        'Products.CMFDiffTool',
        'Products.CMFEditions',
        'Products.CMFFormController',
        'Products.CMFQuickInstallerTool',
        'Products.CMFUid',
        'Products.DCWorkflow',
        'Products.GenericSetup>=1.8.1',
        'Products.MimetypesRegistry',
        # 'Products.PloneLanguageTool',
        'Products.PlonePAS >= 5.0.1',
        'Products.PluggableAuthService',
        'Products.PortalTransforms',
        'Products.ResourceRegistries',
        'Products.SecureMailHost',  # For migration only, when can we remove this?
        'Products.ZCatalog >= 2.13.4',
        'Zope2',
    ],
    entry_points="""
    [z3c.autoinclude.plugin]
    target = plone
    """,
)
