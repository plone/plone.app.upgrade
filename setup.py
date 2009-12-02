from setuptools import setup, find_packages

version = '1.0a3'

setup(name='plone.app.upgrade',
      version=version,
      description="Upgrade machinery for Plone.",
      long_description=open("README.txt").read() + "\n" +
                       open("CHANGES.txt").read(),
      classifiers=[
        'Framework :: Plone',
      ],
      keywords='Plone upgrade migration',
      author='Plone Foundation',
      author_email='plone-developers@lists.sourceforge.net',
      url='http://pypi.python.org/pypi/plone.app.upgrade',
      license='GPL',
      packages=find_packages(exclude=['ez_setup']),
      namespace_packages = ['plone', 'plone.app'],
      include_package_data=True,
      zip_safe=False,
      extras_require=dict(
        test=[
            'Products.CMFQuickInstallerTool',
            'Products.PloneTestCase',
            'plone.contentrules',
            'plone.app.i18n',
            'plone.app.redirector',
            'plone.app.viewletmanager',
        ]
      ),
      install_requires=[
        'setuptools',
        'borg.localrole',
        'plone.portlets',
        'plone.session',
        'plone.app.portlets',
        'zope.component',
        'zope.app.cache',
        'zope.app.component',
        'zope.ramcache',
        'Plone',
        'Products.Archetypes',
        'Products.ATContentTypes',
        'Products.contentmigration',
        'Products.CMFActionIcons',
        'Products.CMFCalendar',
        'Products.CMFCore',
        'Products.CMFDefault',
        'Products.CMFDiffTool',
        'Products.CMFEditions',
        'Products.CMFFormController',
        'Products.CMFPlacefulWorkflow',
        'Products.CMFQuickInstallerTool',
        'Products.CMFUid',
        'Products.DCWorkflow',
        'Products.GenericSetup',
        'Products.MimetypesRegistry',
        'Products.PloneLanguageTool',
        'Products.PlonePAS',
        'Products.PortalTransforms',
        'Products.ResourceRegistries',
        'Products.SecureMailHost', # For migration only, when can we remove this?
        'Acquisition',
        'Zope2',
      ],
      entry_points="""
      [z3c.autoinclude.plugin]
      target = plone
      """,
      )
