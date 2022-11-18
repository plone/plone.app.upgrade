from setuptools import find_packages
from setuptools import setup


version = "3.0.0rc1"

setup(
    name="plone.app.upgrade",
    version=version,
    description="Upgrade machinery for Plone.",
    long_description=(open("README.rst").read() + "\n" + open("CHANGES.rst").read()),
    classifiers=[
        "Development Status :: 6 - Mature",
        "Environment :: Web Environment",
        "Framework :: Plone",
        "Framework :: Plone :: 6.0",
        "Framework :: Plone :: Core",
        "Framework :: Zope :: 5",
        "License :: OSI Approved :: GNU General Public License v2 (GPLv2)",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    keywords="Plone upgrade migration",
    author="Plone Foundation",
    author_email="plone-developers@lists.sourceforge.net",
    url="https://pypi.org/project/plone.app.upgrade/",
    license="GPL version 2",
    packages=find_packages(),
    namespace_packages=["plone", "plone.app"],
    include_package_data=True,
    zip_safe=False,
    extras_require=dict(
        test=[
            "plone.app.testing",
            "plone.app.redirector",
        ]
    ),
    install_requires=[
        "setuptools",
        "plone.base",
        "plone.registry",
        "plone.folder",
        "plone.uuid",
        "transaction",
        "zope.component",
        "zope.interface",
        "Acquisition",
        "Products.CMFPlone>=6.0.0a1",
        "Products.CMFCore",
        "Products.CMFEditions",
        "Products.GenericSetup",
        "Products.PlonePAS",
        "Products.ZCatalog",
        "ZODB",
        "Zope>=5.5",
        "plone.app.theming",
    ],
    entry_points="""
    [z3c.autoinclude.plugin]
    target = plone
    """,
)
