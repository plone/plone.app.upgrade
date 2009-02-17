from setuptools import setup, find_packages

version = '0.1'

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
            'Products.PloneTestCase',
        ]
      ),
      install_requires=[
        'setuptools',
        'plone.portlets',
        'plone.app.portlets',
        'zope.component',
        'Plone',
        'Products.CMFCore',
        'Products.CMFEditions',
        'Products.CMFPlacefulWorkflow',
        'Products.GenericSetup',
        'Products.PlonePAS',
        'Acquisition',
        'Zope2',
      ],
      )
