from pathlib import Path
from setuptools import find_packages
from setuptools import setup


version = "3.3.1"

long_description = (
    f"{Path('README.rst').read_text()}\n{Path('CHANGES.rst').read_text()}\n"
)

setup(
    name="plone.app.upgrade",
    version=version,
    description="Upgrade machinery for Plone.",
    long_description=long_description,
    classifiers=[
        "Development Status :: 6 - Mature",
        "Environment :: Web Environment",
        "Framework :: Plone",
        "Framework :: Plone :: 6.0",
        "Framework :: Plone :: 6.1",
        "Framework :: Plone :: Core",
        "Framework :: Zope :: 5",
        "License :: OSI Approved :: GNU General Public License v2 (GPLv2)",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
    ],
    keywords="Plone upgrade migration",
    author="Plone Foundation",
    author_email="plone-developers@lists.sourceforge.net",
    url="https://pypi.org/project/plone.app.upgrade/",
    license="GPL version 2",
    packages=find_packages("src"),
    namespace_packages=["plone", "plone.app"],
    package_dir={"": "src"},
    include_package_data=True,
    zip_safe=False,
    extras_require=dict(
        test=[
            "packaging",
            "plone.app.testing",
            "plone.app.redirector",
            "Products.MimetypesRegistry",
        ]
    ),
    python_requires=">=3.9",
    install_requires=[
        "setuptools",
        "plone.app.caching",
        "plone.app.redirector",
        "plone.base",
        "plone.behavior",
        "plone.dexterity",
        "plone.registry",
        "plone.indexer",
        "plone.folder",
        "plone.uuid",
        "transaction",
        "zope.component",
        "zope.interface",
        "Acquisition",
        "Products.CMFPlone>=6.0.0a1",
        "Products.CMFCore",
        "Products.GenericSetup",
        "Products.PlonePAS",
        "Products.ZCatalog",
        "zc.relation",
        "ZODB",
        "Zope>=5.5",
        "zope.intid",
    ],
    entry_points="""
    [z3c.autoinclude.plugin]
    target = plone
    """,
)
