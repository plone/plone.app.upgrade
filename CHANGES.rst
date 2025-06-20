Changelog
=========

.. You should *NOT* be adding new change log entries to this file.
   You should create a file in the news directory instead.
   For helpful instructions, please see:
   https://github.com/plone/plone.releaser/blob/master/ADD-A-NEWS-ITEM.rst

.. towncrier release notes start

3.2.2 (2025-06-20)
------------------

Bug fixes:


- Do not "fix" menubar value of ITinyMCESchema if it is already a string.
  [maurits] (#340)


3.2.1 (2025-06-20)
------------------

Bug fixes:


- add upgrade step to fix menubar value of ITinyMCESchema, value is now a string, not a list
  [1letter] (#340)
- Harden condition of external editor action to not fail when the ``externalEditorEnabled`` script is not available.
  [maurits] (#4179)


Internal:


- Added upgrade to 6027, Plone 6.0.16.
  [maurits] (#6027)
- Added upgrade to 6109, Plone 6.1.2.
  [maurits] (#6109)


3.2.0 (2025-03-14)
------------------

New features:


- Prepare a folder for the 6.2 upgrade steps


Bug fixes:


- Replace `pkg_resources` with `importlib.metadata`/`packaging` @gforcada (#4126)


Internal:


- Added upgrade to 6108, Plone 6.1.1.
  [maurits] (#6108)


3.1.9 (2025-01-31)
------------------

Bug fixes:


- Ensure that the mimetypes registry globs contain valid patterns (#333)
- Fix DeprecationWarnings. [maurits] (#4090)


Internal:


- Added upgrade to 6026, Plone 6.0.15.
  [maurits] (#6026)
- Added upgrade to 6107, Plone 6.1.0rc1 and 6.1.0 final.
  [maurits] (#6107)


3.1.8 (2024-12-19)
------------------

Internal:


- Added upgrade to 6106, Plone 6.1.0b2.
  [maurits] (#6106)


Tests


- Fix removed `unittest.makeSuite` in python 3.13.
  [petschki] (#331)


3.1.7 (2024-10-31)
------------------

Internal:


- Added upgrade to 6025, Plone 6.0.14.
  [maurits] (#6025)
- Added upgrade to 6105, Plone 6.1.0b1.
  [maurits] (#6105)


3.1.6 (2024-09-05)
------------------

Bug fixes:


- 6.1: Cleanup ``plone.app.discussion`` settings when the package is not available.
  If the site contains comments, we throw an error and stop the upgrade.
  The advice then is to add the ``plone.app.discussion`` package.
  [maurits] (#211)


Internal:


- Added upgrade to 6024, Plone 6.0.13.
  [maurits] (#6024)
- Added upgrade to 6104, Plone 6.1.0a5.
  [maurits] (#6104)


3.1.5 (2024-08-01)
------------------

Bug fixes:


- Fix upgrading `plone.app.iterate` to specific version.
  In Plone 6.1 the deprecated GS profile with id `plone.app.iterate` has been removed, and only `default` remains, as is usual.
  [maurits] (#99)
- 6.1: Remove the portal_properties tool completely.
  This tool is deprecated, and we said we would remove it in 6.1.
  [maurits] (#125)
- 6.1: Add upgrade step that removes After the Deadline settings.
  [reinhardt] (#328)


Internal:


- Added upgrade to 6023, Plone 6.0.12.
  [maurits] (#6023)
- Added upgrade to 6103, Plone 6.1.0a4.
  [maurits] (#6103)


3.1.4 (2024-04-25)
------------------

Bug fixes:


- Add upgrade step for enable TinyMCE Plugin accordion to v60
  [1letter] (324-1)
- Add upgrade step for enable TinyMCE Plugin accordion
  [1letter] (#324)
- Add upgrade to add registry record ``webstats_head_js`` to ``ISiteSchema``.
  [maurits] (#3931)


Internal:


- Added upgrade to 6022, Plone 6.0.11.
  [maurits] (#6022)
- Added upgrade to 6102, Plone 6.1.0a3.
  [maurits] (#6102)


3.1.3 (2024-02-22)
------------------

Bug fixes:


- Update TinyMCE format icon names.
  [petschki, maurits] (#3095)
- Added upgrade to 6101, Plone 6.1.0a2.
  [maurits] (#6101)


3.1.2 (2024-01-26)
------------------

Bug fixes:


- Remove Archetypes modifiers from portal_modifier early in Plone 6.0 alpha.
  CMFEditions already tried to do this, but this might fail in a corner case.
  [maurits] (#6003)


Internal:


- Added upgrade to 6021, Plone 6.0.10.
  [maurits] (#6021)


3.1.1 (2023-12-14)
------------------

Internal:


- Added upgrade to 6020, Plone 6.0.9.
  [maurits] (#6020)


3.1.0 (2023-10-26)
------------------

New features:


- Added upgrade to 6100, Plone 6.1.0a1.
  [maurits] (#6100)


Bug fixes:


- Added upgrade to 6019, Plone 6.0.8.
  [maurits] (#6019)


3.0.8 (2023-09-20)
------------------

Bug fixes:


- Fix error in site syndication settings when upgrading.
  [maurits] (#315)


3.0.7 (2023-09-14)
------------------

Bug fixes:


- Add Upgrade Step to fix ISyndicationSettings
  [1letter] (#315)
- Added upgrade to 6018, Plone 6.0.7.
  [maurits] (#6018)


3.0.6 (2023-06-22)
------------------

Bug fixes:


- Added upgrade to 6017, Plone 6.0.6.  [maurits] (#6017)


3.0.5 (2023-05-30)
------------------

Bug fixes:


- Fix TinyMCE problem: Tools and View do not show up in menubar.
  The menubar contained "toolsview" instead.
  [maurits] (#3785)
- Added upgrade to 6016, Plone 6.0.5.  [maurits] (#6016)


3.0.4 (2023-04-21)
------------------

Bug fixes:


- Added upgrade to 6015, Plone 6.0.4.  [maurits] (#6015)


3.0.3 (2023-03-23)
------------------

Bug fixes:


- Import more from plone.base. [maurits] (#1)
- Fix plone.app.iterate profiles.
  [maurits] (#99)
- Add Site Administrator role to various permissions.
  [maurits] (#3225)
- Added upgrade to 6014, Plone 6.0.3.  [maurits] (#6014)


3.0.2 (2023-02-23)
------------------

Bug fixes:


- Add two missing upgrades steps to Plone 5.2.10 and 5.2.11.
  [maurits] (#5211)
- Added upgrade to 6013, Plone 6.0.2.  [maurits] (#6013)


3.0.1 (2023-01-30)
------------------

Bug fixes:


- Add `autolink` plugin to `ITinyMCESchema.plugins`.
  [petschki] (#308)
- Added upgrade to 6012, Plone 6.0.1.  [maurits] (#6012)


3.0.0 (2022-12-12)
------------------

Bug fixes:


- Added upgrade to 6011, Plone 6.0.0 final.  [maurits] (#6011)


3.0.0rc2 (2022-12-05)
---------------------

Bug fixes:


- Apply volto.blocks behavior if the site was being used as a Volto site
  [erral] (#304)
- Catch KeyError when getting object from a brain, and ignore this brain.
  Log a warning.
  [maurits] (#306)
- Added upgrade to 6010, Plone 6.0.0rc2.  [maurits] (#6010)


3.0.0rc1 (2022-11-18)
---------------------

Bug fixes:


- Added upgrade to 6009, Plone 6.0.0rc1. (#6009)


3.0.0b5 (2022-10-04)
--------------------

Bug fixes:


- Update plonetheme.barceloneta registry.
  [petschki] (#302)
- Added upgrade to 6008, Plone 6.0.0b3. (#6008)


3.0.0b4 (2022-09-10)
--------------------

Bug fixes:


- Add migration of actions.xml for https://github.com/plone/Products.CMFPlone/pull/3616
  Add infrastructure for to beta2 migrations.
  [jensens] (#294)
- Add a timezone property to portal memberdata if it is missing. (#295)
- Update the portal actions icon expressions
  [ale-rt] (#298)
- Add an upgrade step to fix the dexterity indexer behavior (#300)
- Added upgrade to 6007, Plone 6.0.0b2.  [maurits] (#6007)


3.0.0b3 (2022-07-23)
--------------------

Bug fixes:


- Added upgrade to 6006, Plone 6.0.0b1.  [maurits] (#6006)


3.0.0b2 (2022-06-24)
--------------------

Bug fixes:


- ``update_catalog_metadata``: catch and log ``ComponentLookupError`` when getting indexable object.
  [maurits] (#3521)


3.0.0b1 (2022-06-24)
--------------------

Breaking changes:


- Removed old code, aliases and dependencies.
  This were only needed to have a clean upgrade to earlier Plone versions.
  We only support upgrading from Plone 5.2 Python 3.
  [maurits] (#286)


New features:


- Upgrade profiles of core Plone modules to specific versions.
  See `issue 3346 <https://github.com/plone/Products.CMFPlone/issues/3346>`_.
  [maurits] (#3346)
- Add ``image_scales`` catalog metadata column.
  Update all brains to get this info.
  Since this takes long on large sites, you can disable this with an environment variable:
  ``export UPDATE_CATALOG_FOR_IMAGE_SCALES=0``
  In that case, you are advised to add the ``image_scales`` column manually to the catalog later.
  [maurits] (#3521)


Bug fixes:


- Cleanup: pyupgrade, isort, black.  [maurits] (#287)
- Add upgrade-profile for 6005 and reload tinyconfig to allow inline-mode.
  [pbauer] (#288)
- Remove empty ``plone_templates`` skin layer.
  [maurits] (#3515)
- Added upgrade to 6005, Plone 6.0.0a5.  [maurits] (#6005)


3.0.0a4 (2022-04-08)
--------------------

New features:


- Add upgrades to migrate existing site to es6. [pbauer] (#269)
- Add plone-view icon.
  Ref: https://github.com/plone/plone.staticresources/commit/59bb178620b186f07a058cedefeeec1039f5c821
  [thet] (#279)
- Reload ISearchSettings to add support for images in liveSearch results.
  [agitator+maurits] (#3489)


Bug fixes:


- Remove old ``plone.session`` bundles.
  Reapply its new registry settings, if its optional refresh support is installed.
  Part of `plone.session issue 24 <https://github.com/plone/plone.session/issues/24>`_.
  [maurits] (#24)
- Upgrade step to remove the removed viewlet plone.header
  [erral] (#268)
- Fix several exceptions when calling ``fix_unicode_properties``.
  Depend on Zope 5.5 to use its official version of this function.
  [maurits] (#270)
- Added upgrade to remove Configlets "Change Member Password" and "Member Prefs"
  [1letter] (#272)
- Do not reload plone-logged-in during upgrade. Add jquery bundle.
  [pbauer] (#277)
- Add eventedit bundle on upgrade.
  [pbauer] (#278)
- Clear out plone.content_css
  [pbauer] (#280)
- Remove deprecated `conditionalcomment` field from IBundleRegistry
  [petschki] (#283)
- Removed empty skin layers ``plone_prefs`` and ``plone_form_scripts``.
  [maurits] (#3240)
- Add new image scales.
  [maurits] (#3279)
- Added upgrade to 6004, Plone 6.0.0a4.  [maurits] (#6004)


3.0.0a3 (2022-01-28)
--------------------

Bug fixes:


- Rerelease without changes as 3.0.0a3 so it fits better with the Plone 6.0.0a3 version.
  It is not guaranteed to keep matching.
  [maurits] (#300)


3.0.0a2 (2022-01-28)
--------------------

Bug fixes:


- Upgrade Step for renamed error-log-form view link in ControlPanel
  [jmevissen] (#266)
- Fix unicode properties.
  See `issue 3305 <https://github.com/plone/Products.CMFPlone/issues/3305>`_.
  [maurits] (#3305)
- Added upgrade to 6003, Plone 6.0.0a3.  [maurits] (#6003)


3.0.0a1 (2021-12-03)
--------------------

Breaking changes:


- Removed upgrade steps from Plone 5.1 and lower.
  You can only migrate to Plone 6 from a site that is already Python 3, so Plone 5.2.
  [maurits] (#227)


Bug fixes:


- Index the Plone site root (#264)
- Added upgrade to 6002, Plone 6.0.0a2.  [maurits] (#6002)


2.0.41 (2021-10-16)
-------------------

Bug fixes:


- Add an UUID to existing, migrated site roots. [jensens] (#258)
- Add upgrade to 5214, Plone 5.2.6.
  [maurits] (#5214)
- Renamed ``v60/profiles/to_alpha1`` to ``to6000``.
  We have no Plone alpha1 release yet, but do have a pre alpha.
  [maurits] (#6000)
- Added upgrade to 6001, Plone 6.0.0a1.dev1.
  [maurits]

  Fix icon_expr in typeinfo action
  [petschki] (#6001)


2.0.40 (2021-09-16)
-------------------

Breaking changes:


- Upgrade step to make the Plone site a dexterity object (#256)


New features:


- Protect @@historyview with Modify portal content permission. Fixes https://github.com/plone/Products.CMFPlone/issues/3297
  [pbauer] (#254)
- Add relations controlpanel as part of https://github.com/plone/Products.CMFPlone/pull/3232
  [pbauer] (#255)


Bug fixes:


- Added upgrade to 6000, Plone 6.0.0a1.dev0.
  [maurits] (#600)


2.0.39 (2021-07-31)
-------------------

Bug fixes:


- Added upgrade to 5213, Plone 5.2.5.
  [maurits] (#525)


2.0.38 (2021-03-02)
-------------------

Bug fixes:


- Make portal_setup objects accessible only to Manager/Owner.
  See `GenericSetup issue 101 <https://github.com/zopefoundation/Products.GenericSetup/issues/101>`_.
  [maurits] (#101)


2.0.37 (2021-02-19)
-------------------

Breaking changes:


- Remove temp_folder from Zope root if broken.
  See `issue 2957 <https://github.com/plone/Products.CMFPlone/issues/2957>`_.
  [maurits] (#2957)


Bug fixes:


- Plone 6.0: remove portal_form_controller tool.
  [maurits] (#3057)
- Improved upgrade step for site_logo from ASCII to Bytes.
  The previous upgrade was incomplete and could remove the logo when called twice.
  See `comment on issue 3172 <https://github.com/plone/Products.CMFPlone/issues/3172#issuecomment-733085519>`_.
  [maurits] (#3172)


2.0.36 (2020-10-30)
-------------------

Breaking changes:


- 6.0 alpha 1: remove the portal_quickinstaller tool.
  See `PLIP 1775 <https://github.com/plone/Products.CMFPlone/issues/1775>`_.
  [maurits] (#1775)


2.0.35 (2020-09-21)
-------------------

Bug fixes:


- Replaced import of plone.api, which should not be used by core.
  [maurits] (#241)
- Fixes a rare case in v52/betas while migration of relations: Missing attributes on cataloged relations are safely ignored.
  [jensens] (#244)
- Plone 5.1.7: Update resource registry ``last_compilation`` date.
  [maurits] (#1006)
- Catch deprecation warnings for ``webdav.LockItem.LockItem`` and ``CMFPlone.interfaces.ILanguageSchema``.
  The first has been moved to ``OFS.LockItem``, the second to ``plone.i18n.interfaces``.
  In older upgrade code, we should still try the old import first.
  Fixed deprecation warning for zope.site.hooks.
  Fixed invalid escape sequence.
  [maurits] (#3130)
- Migrate the ``plone.site_logo`` field from ASCII (native string) to Bytes.
  Otherwise saving the site-controlpanel can fail with a WrongType error
  Fixes `issue 3172 <https://github.com/plone/Products.CMFPlone/issues/3172>`_.
  [maurits] (#3172)


2.0.34 (2020-08-16)
-------------------

Bug fixes:


- Plone 5.1.7: Update resource registry ``last_compilation`` date.
  [vincentfretin] (#236)


2.0.33 (2020-06-30)
-------------------

Bug fixes:


- Fix UnicodeDecodeError in move_dotted_to_named_behaviors when migrating behaviors for content_types where the fti has a special character.
  [pbauer] (#235)


2.0.32 (2020-06-28)
-------------------

New features:


- Add upgrade step for Plone 5.2.2.
  [thet]

  Image caption support
  Allow ``figcaption`` in rich text editor as a valid tag.
  Add registry setting for plone.image_caption outputfilter transform.
  [thet] (#209)
- Add upgrade step to migrate markdown tranform settings to markup control panel.
  [thomasmassmann] (#228)
- Add upgrade profiles for v60, including a upgrade step for #3086 (custom.css view)
  [MrTango] (#3086)


Bug fixes:


- Fix problem in step to 5.2 beta 1 `remove_interface_indexes_from_relations_catalog`.
  While upgrading the relation-catalog in some real world databases some of the iterated tokens are orphaned.
  Remove them to have a clean relation-catalog afterwards and log a warning.
  [jensens] (#225)
- add upgrade steps for HTMLFilter defaults.
  [petschki] (#233)

For 2.0.31 and earlier changes, see the `2.x branch <https://github.com/plone/plone.app.upgrade/blob/2.x/CHANGES.rst>`_.
