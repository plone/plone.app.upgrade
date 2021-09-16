Changelog
=========

.. You should *NOT* be adding new change log entries to this file.
   You should create a file in the news directory instead.
   For helpful instructions, please see:
   https://github.com/plone/plone.releaser/blob/master/ADD-A-NEWS-ITEM.rst

.. towncrier release notes start

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


2.0.31 (2019-12-15)
-------------------

Bug fixes:


- Make sure plone.staticresources is installed to fix issues with site migrated from 5.0 or 5.1 to 5.2.1.
  Fixes https://github.com/plone/Products.CMFPlone/issues/2996
  [pbauer] (#223)


2.0.30 (2019-12-13)
-------------------

Bug fixes:


- Fixed error when upgrading relations.
  [maurits] (#220)


2.0.29 (2019-12-02)
-------------------

Bug fixes:


- Add Collection to the default_page_types setting
  [erral] (#216)


2.0.28 (2019-09-03)
-------------------

Bug fixes:


- Add empty upgrade step for Plone 5.1.6 
  [esteele] (#214)


2.0.27 (2019-07-10)
-------------------

Bug fixes:


- Add upgrade step for Plone 5.2 final
  [esteele] (#213)


2.0.26 (2019-06-27)
-------------------

Bug fixes:


- Add empty upgrade step for Plone 5.2rc5
  [esteele] (#212)


2.0.25 (2019-06-19)
-------------------

New features:


- Upgrade step for optional async loading
  [agitator] (#208)
- In registry move all interface prefixes for ``ILanguageSchema`` from old place in Products.CMFPlone to plone.i18n.
  [jensens] (#210)


Bug fixes:


- Fix upgrades from Plone 4.3 to 5.2.
  [pbauer] (#207)
- Reload ISecuritySchema to create plone.autologin_after_password_reset key for Plone 5.2.
  [jensens, agitator, maurits] (#2440)


2.0.24 (2019-05-04)
-------------------

New features:


- Added upgrade step to initialize the date and manual information for redirects.
  [maurits] (#2799)


Bug fixes:


- Fix changing bucket size while reindexing relation catalog.
  [jensens] (#201)
- Add alias for webdav.LockItem.LockItem. Fixes https://github.com/plone/Products.CMFPlone/issues/2800
  [pbauer] (#203)
- Moved dotted named behaviors to named behaviors.
  [iham] (#204)


2.0.23 (2019-03-21)
-------------------

Bug fixes:


- Add upgrade steps for PLIP 1653. [thet] (#184)
- Add upgrade profile for Plone 5.2beta2
  [davilima6]

  Add upgrade step for loading Moments.js without locales, which are now lazy loaded
  [davilima6] (#199)
- Fix changing bucket size while reindexing relation catalog.
  [jensens] (#201)


2.0.22 (2019-03-04)
-------------------

Bug fixes:


- Fixed permission error while removing old resource registries. [maurits]
  (#197)
- Add bbb for CSSRegistryTool and JSRegistryTool to fix upgrade from 5.0 to 5.2
  (#200)


2.0.21 (2019-02-13)
-------------------

New features:


- Added URL Management controlpanel and object_button action. [maurits] (#1486)


Bug fixes:


- Tolerate lack of legacy resource registry [ksuess] (#183)
- Add missing upgrade step for CMFEditions [MrTango] (#188)
- Provide upgrade step that purges and rebuild the _members data structure in
  portal_memberdata [pysailor] (#190)
- Update all FTIs that use the RichText or LeadImage behaviors (#192)
- Add alias for GopipIndex to fix migrations to 5.2 (#193)
- Remove interface indexes from relation catalog [jmevissen] (#195)


2.0.20 (2018-12-30)
-------------------

Bug fixes:


- Plone 5.1.5: Update resource registry ``last_compilation`` date. [thet]
  (#186)


2.0.19 (2018-12-10)
-------------------

Bug fixes:


- migrate GopipIndex which has moved from p.a.folder to p.folder [petschki]
  (#177)
- Do not break if archetypes related code is not available [ale-rt, pbauer]
  (#178)
- tolerate lack of legacy resource registry [ksuess] (#182)


2.0.16 (2018-10-01)
-------------------

New features:


- Add upgrade steps for Datatables on Plone 5.1.4. [frapell] (#168)
- Add upgrade step removing the jquery-highlightsearchterms resource and the
  plone_ecmascript skin layer, on Plone 5.2 and 5.1.4 [sunew] (#170)
- Update bundle dates after recompilation in CMFPlone. [sunew] (#171)
- Added upgrade for TinyMCE 4.7.13 on Plone 5.0.10. [obct537] (#174)


Bug fixes:


- Update resources for plone.app.event. [agitator] (#166)
- Prepare for Python 2 / 3 compatibility [ale-rt, pbauer, tlotze] (#173)
- make `plone.app.folder` import conditional, because the package is gone in
  Plone >= 5.2 [petschki] (#175)
- fix tests in Plone >= 5.2 and python 3. As discussed with jensens and
  mauritsvanrees we start migration tests beginning from 4.0 final due to
  portal_factory property errors. [petschki] (#176)


2.0.15 (2018-06-21)
-------------------

New features:

- Merge plone.login and remove skins folder plone_login.
  [jensens]

Bug fixes:

- Made several functions less complex by splitting them.  [maurits]

- Improved code quality.  [maurits]


2.0.14 (2018-04-09)
-------------------

Bug fixes:

- Fix i18n domain for some portal_actions that were on plone.app.event domain.
  Fixes https://github.com/plone/plone.app.event/pull/204
  [gforcada]


2.0.13 (2018-04-08)
-------------------

Bug fixes:

- Change in TinyMCE css location so bundles can be built without errors
  Fixes `issue 2359 <https://github.com/plone/Products.CMFPlone/issues/2359>`_.
  [frapell]


2.0.12 (2018-03-10)
-------------------

Bug fixes:

- Rename retina_scales to highpixeldensity_scales.
  Fixes `issue 2331 <https://github.com/plone/Products.CMFPlone/issues/2331>`_.
  [maurits]

- Hide our 'products' from installation for both CMFQuickInstallerTool and CMFPlone.
  [maurits]


2.0.11 (2018-02-05)
-------------------

Bug fixes:

- Removed hard dependency on ``CMFQuickInstallerTool``.
  And marked the v52 module as non installable.  [maurits]

- Import ``setupPasswordPolicyPlugin`` from canonical place in ``PlonePAS``.
  [maurits]

- Log progress and ignore bad catalog entries while updating catalog metadata.
  [davisagli]

- Disable CSRF protection when replacing keyring.
  This fixes running specific upgrade steps via the portal_setup UI.
  [davisagli]

- Avoid triggering an unnecessary migration of user logins
  when the use_email_as_login setting is migrated to portal_registry.
  [davisagli]


2.0.10 (2017-12-13)
-------------------

Bug fixes:

- Unregister import_steps that were moved to post_handlers.
  Fixes https://github.com/plone/Products.CMFPlone/issues/2238
  [pbauer]


2.0.9 (2017-11-26)
------------------

New features:

- Add upgrade step for 5.2 to register tools as utilities.
  Run it before testing the zexp-import.
  [pbauer]

Bug fixes:

- Fixed WrongType exception when migrating installed Iterate to 5.0.
  [maurits]

- Adapt to changes in CMF 2.4 (getCurrentKeyFormat removed) and Zope 4 (not Products in Control Panel).
  [pbauer]

- Register upgrades for Plone 5.2
  [pbauer]

- Fix installation of IUserGroupsSettingsSchema into registry for Plone 5.0rc1.
  [davisagli]

- Avoid swallowing errors during registry setting upgrades.
  [davisagli]

2.0.8 (2017-09-25)
------------------

Bug fixes:

- Fix deletion of registry records in ``remove_duplicate_iterate_settings``
  from the ``5108`` upgrade.
  [thet]

- Register Plone 5.1 upgrade steps.
  [thet]

- Register settings for safe_html-Transform when migrating from 5107 to 5108
  [pbauer]

- Use str() when migrating checkout_workflow_policy since the field is ASCII.
  See discussion at https://github.com/plone/plone.app.iterate/pull/53
  [pbauer]

- Use safe_unicode to migrate some settings. Fixes https://github.com/plone/plone.app.upgrade/issues/104
  [pbauer]

2.0.7 (2017-09-10)
------------------

New features:

- Add jqtree-contextmenu to the resource registry for Plone 5.0 and 5.1
  [b4oshany]

- Add js-shortcuts to the resource registry for Plone 5.0 and 5.1
  [b4oshany]

Bug fixes:

- Recover missing dashboard (user actions)
  https://github.com/plone/Products.CMFPlone/issues/1132
  [fgrcon]

- Register settings for safe_html-Transform before linkintegrity-migration in 5.0rc1
  Fixes https://github.com/plone/Products.CMFPlone/issues/2129
  [pbauer]

- Fix migration if safe_html-Settings to not drop tags without a closing tag.
  Fixes https://github.com/plone/Products.CMFPlone/issues/2088
  [pbauer]

- Cleanup duplicate iterate settings. See also https://github.com/plone/plone.app.iterate/pull/47
  [pbauer]


2.0.6 (2017-08-05)
------------------

New features:

- Added ``Show Toolbar`` permission.
  [agitator]

Bug fixes:

- Fix #84 - usage of aq_base
  [jensens]


2.0.5 (2017-07-03)
------------------

Bug fixes:

- Plone 5.1: Fixup timezone record fields, as old interface
  plone.app.event.bbb.interfaces.IDateAndTimeSchema is gone since
  plone.app.event 3.0.2.
  [thet]

- Fix upgrade step for ISocialMediaSchema
  [MrTango]


2.0.4 (2017-06-04)
------------------

New features:

- New Options for thumb- and icon-handling in site control panel
  https://github.com/plone/Products.CMFPlone/issues/1734
  upgradesteps to 5.1b4
  [fgrcon]

- TinyMCE 4.5.6 update.
  [thet]

- Update registry for Plone 5.1 to integrate ``mockup-patterns-structureupdater``.
  [thet]

Bug fixes:

- Register ``ISiteSyndicationSettings`` again.
  This interface was updated in 5.0rc3.
  On older sites, this would cause an error on the ``syndication-controlpanel``:
  KeyError: 'Interface `Products.CMFPlone.interfaces.syndication.ISiteSyndicationSettings` defines a field `render_body`, for which there is no record.
  [maurits]

- Catch warning the pythonic way.
  Makes it work with latest CMFCore.
  [jensens]

- Fix and ``AttributeError`` for the Plone 5.1 beta 4 upgrade.
  [thet]


2.0.3 (2017-04-18)
------------------

New features:

- Add Plone 5.1 beta 4 upgrade profile.
  [thet]

- new metadata catalog column mime_type
  https://github.com/plone/Products.CMFPlone/issues/1995
  [fgrcon]

Bug fixes:

- Do not convert/fail on None while update_social_media_fields
  [agitator]

- Fixed ImportError when ``Products.ATContentTypes`` is not available.
  This happens when you only have the ``Products.CMFPlone`` egg
  and not the ``Plone`` egg.  [maurits]

- Fixed title and description of plone.resource.maxage.
  This had the title and description from shared maxage,
  due to a wrong reference.
  See https://github.com/plone/Products.CMFPlone/issues/1989
  [maurits]

- Removed "change portal events"
  [kakshay21]

2.0.2 (2017-04-03)
------------------

New features:

- Add image scaling options to image handling controlpanel
  when migrating to 5.1b3.
  [didrix]

Bug fixes:

- Update ``twitter_username``, ``facebook_app_id`` and ``facebook_username`` field values as they are now declared as ``ASCIILine`` instead of ``TextLine``.
  [hvelarde]


2.0.1 (2017-03-09)
------------------

Bug fixes:

- Adapt tests to the new indexing operations queueing.
  Part of PLIP 1343: https://github.com/plone/Products.CMFPlone/issues/1343
  [gforcada]

- Fix registration of upgrade-step to Plone 5.1a1
  [pbauer]

2.0.0 (2017-02-20)
------------------

Breaking changes:

- Remove really old upgrade steps (everything up to v40).
  [gforcada]

New features:

- New mockup releases for Plone 5.0 and 5.1.
  [thet]

- Remove jquery.cookie from plone-logged-in bundle's stub_js_modules.
  The toolbar, which has a dependency on jquery.cookie,
  was moved from the plone bundle to plone-logged-in in CMPlone 5.1a2.
  [thet]

- Products.MimetypesRegistry has no longer a skins layer, remove it.
  [jensens]

- Add sort_on field to search controlpanel.
  [rodfersou]

- Support sites without ``portal_quickinstaller``.
  We use ``get_installer`` in Plone 5.1 migrations.
  In earlier version we will keep using the ``portal_quickinstaller``,
  because ``get_installer`` is not available.
  In shared utility and base code, we try to import get_installer,
  and fall back on the previous implementation.
  See `PLIP 1340 <https://github.com/plone/Products.CMFPlone/issues/1340>`_.
  [maurits]

- Add new Mockup 2.4.0 relateditems resource url.
  Add new optional relateditems upload resource.
  [thet]

- Update ``last_compilation`` to deliver new bundles.
  [thet]

- Move PasswordResetTool to CMFPlone.
  *Note: Pending password resets are deleted.*
  [tomgross]

- Adopt to changes in Zope4
  [pbauer]

Bug fixes:

- Remove displayContentsTab from action expressions in 5.1.
  Fixes https://github.com/plone/Products.CMFPlone/issues/1935.
  [maurits]

- Fix move_pw_reset_tool upgrade step
  [agitator]

- Install plone.app.caching in 5.0 alpha if available.
  When it is already installed, upgrade it.
  [maurits]

- Install plone.app.theming in 5.0 alpha.
  When it is already installed, upgrade it.
  [maurits]

- Fixed AttributeError ``use_content_negotiation`` when migrating old language tool.
  Not all versions have the same properties available.
  Now we only take over existing properties.
  5.0 beta.
  [maurits]

- Fixed ConstraintNotSatisfied when default_editor is not allowed.
  5.0 alpha.
  [maurits]

- Enabled update from latest 4.3 profile revision.
  Otherwise we would skip a few upgrade steps when migrating to
  Plone 5.  [maurits]

- Don't remove sub skin layers when cleaning ``portal_skins``.
  Created ``utils.cleanUpSkinsTool`` method which has generally useful
  code for cleaning up the skins.
  Fixes `issue 87 <https://github.com/plone/plone.app.upgrade/issues/87>`_.
  [maurits]

- Install plone.resource in Plone 5.0 alpha 3.  Fixes possible
  ``TypeError: argument of type 'NoneType' is not iterable`` when
  migrating from Plone 4.3 for a site that did not have plone.resource
  or diazo installed yet.
  Fixes `issue 1756 <https://github.com/plone/Products.CMFPlone/issues/1756>`_. [maurits]

- Be sure smtp_port is an integer.
  [ale-rt]

- Fix upgrade step for PasswordResetTool if there was never da different value than the default was set.
  [jensens]

- Check whether avoiding exception in RealUpgradeLayer setup avoids polluting test environment.
  [davisagli]

- avoid error in layer teardown
  [davisagli]

1.3.27 (2016-08-16)
-------------------

Bug fixes:

- Add empty upgrade step for 4.3.11.
  [esteele]

- Add empty upgrade step for 5.0.6.
  [esteele]


1.3.26 (2016-08-15)
-------------------

Bug fixes:

- Remove deprecated ``mockup-registry`` and ``mockup-parser`` resources.
  [thet]

- Update ``last_compilation`` to deliver new bundles.
  [thet]

- Add missing ``jquery.browser`` dependency which is needed by patternslib.
  [thet]

- Use zope.interface decorator.
  [gforcada]

1.3.25 (2016-06-21)
-------------------

New:

- Adds controlpanel setting to enable navigation root bound keyword vocabularies.
  [jensens]

- Update to 5.1a2 upgrade step to allow upgrades from Plone 5.1a1.
  [jensens]


1.3.24 (2016-03-31)
-------------------

New:

- Add actions controlpanel when migrating to 5.1a1.
  [esteele]

- Add null upgrade step for 5.0.3 to 5.0.4
  [esteele]


1.3.23 (2016-03-31)
-------------------

Fixes:

- Update 5.0a1 upgrade step to allow upgrades from Plone 5.0.3.
  [esteele]


1.3.22 (2016-03-29)
-------------------

New:

- Registry upgrades for Plone 5.1 (less variables).
  [jensens]


1.3.21 (2016-02-24)
-------------------

New:

- Registry upgrades for Plone 5.0.3
  [vangheem]

- Hidden the v50 module from the installable products, just like our
  other modules.  [maurits]

Fixes:

- Use `unsetLastVersionForProfile` from GenericSetup 1.8.1 and
  higher.  [maurits]

- Fix ``cleanUpProductRegistry`` to not break when ``Control_Panel`` cannot be found.
  Fixes test failures with Zope 4.
  [thet]


1.3.20 (2016-01-08)
-------------------

Fixes:

- Run missing upgrade-step of plone.app.querystring when upgrading to 5.0.2.
  [pbauer]


1.3.19 (2015-12-17)
-------------------

New:

- reapply profile for site-controlpanel
  plone/Products.CMFPlone#124
  [fgrcon]

- extended step to501 to recreate metadata for getIcon, see
  plone/Products.CMFPlone#1226, #58, #60, #61
  [fgrcon, gagaro, jensens]

- Removed fake kupu tool and related settings and resources.
  [maurits]

- Cleanup the skins tool.
  [maurits]

- Cleanup uninstalled products.  Remove uninstalled products from QI
  and mark their installed profile version as unknown.
  [maurits]

- If non installable profiles (really: hidden profiles) have been
  installed in GS, mark their products as installed in the QI.  This
  does not work when also that *product* is marked as non installable,
  because in normal operation (outside of plone.app.upgrade) this does
  not happen either.
  [maurits]

- Unmark installed profiles that are no longer available.
  [maurits]

Fixes:

- Fixed removal of Large Plone Folder when migrating from Plone 3.
  [maurits]


1.3.18 (2015-09-27)
-------------------

- Add migration for ILinkSchema
  [vangheem]

- Add migration for TinyMCE settings
  [vangheem]

- Fix migration of typesUseViewActionInListings to registry.
  [pbauer]

- Fix incorrect interate import.
  [alecm]


1.3.17 (2015-09-22)
-------------------

- Fix issues with missing registry-entries when upgrading 5.0rc2 -> 5.0rc3.
  [pbauer]


1.3.16 (2015-09-20)
-------------------

- Plone 4.3: upgrade TinyMCE correctly.  Update sunburst theme profile
  version when applying its upgrade step.  Update CMFEditions.  Update
  plone.app.jquery.
  This fixes
  https://github.com/plone/Products.CMFPlone/issues/812
  [maurits]

- Portal properties calendar_starting_year and calendar_future_years_available
  were moved to registry.
  [pbauer]

- Remove unused invalid_ids portal property
  [esteele]


1.3.15 (2015-09-11)
-------------------

- Fix migration of types_not_searched to registry.
  Fixes https://github.com/plone/plone.app.contenttypes/issues/268
  [pbauer]

- Remove site properties that have been migrated to the registry.
  [esteele]


1.3.14 (2015-09-08)
-------------------

- Remove no-longer-used properties from portal_properties
  [esteele]

- Remove plone_forms skins folder for 5.0 rc1
  [esteele]

- Install plone.app.linkintegrity and migrate linkintegrity-relations.
  [pbauer]


1.3.13 (2015-08-23)
-------------------

- Unregister removed collection.css.
  [pbauer]

- 5.0 beta: do not set ``url_expr`` on configlet.  This must be done
  with ``setActionExpression``.
  Fixes https://github.com/plone/Products.CMFPlone/issues/814
  [maurits]

- Turn @@tinymce-controlpanel ``content_css`` field into a list
  [ebrehault]


1.3.12 (2015-07-23)
-------------------

- Fix for 5.0b2 -> 5.0b3 upgrade step that removed permissions from most of
  the control panel configlets. This fixes:
  https://github.com/plone/Products.CMFPlone/issues/745
  [sneridagh, timo]


1.3.11 (2015-07-20)
-------------------

- upgrade plone buttons to not have so many things open in modals
  [vangheem]

- uninstall mockup-pattern-accessibility pattern registration
  [vangheem]

- add Products.CMFPlacefulWorkflow as dep as __init__ requires this
  [maartenkling]

- add social media control panel upgrade
  [vangheem]

- upgrades for plone 5 tinymce configuration and social tags config
  [vangheem]

- add step for updated dropzone resource location
  [vangheem]

- remove plone.app.jquery dependency
  [vangheem]

- Add jquerytools removal upgrade
  [vangheem]

- Plone 5: upgrade manage portlets js
  [vangheem]

- Remove hard dependency on CMFDefault
  [tomgross]

- Update the category configlet of all the configlets in order to provide a way
  to categorize properly each configlet [sneridagh]

- Updated links for the renamed 'Types' control panel [sneridagh]


1.3.10 (2015-05-13)
-------------------

- Plone 4.3: Enable NewsML feed syndication
  [tcurvelo]

- Plone 5: Migrate imagine control panel settings to the configuration
  registry
  [vangheem]

- Plone 5: Solve CMFPlacefulWorkflow __iro__ problem because
  of moving their paths when upgrading
  [bloodbare]


1.3.9 (2015-03-26)
------------------

- LanguageTool/plone.app.multilingual migration
  [bloodbare]

- Update tests after removal of ``allowAnonymousViewAbout`` and
  ``validate_email`` properties in CMFPlone.
  [jcerjak]

- Do not run tests not suited for the current Plone version
  (implemented for 4.0 and below)
  [jensens]

- Add upgrade step for the security control panel.
  [jcerjak]

- Add upgrade step for mail control panel. Refs PLIP 10359.
  [jcerjak, khink]

- Add upgrade steps for markup control panel.
  [thet]


1.3.8 (2014-11-01)
------------------

- Add upgrade steps for editing, maintenance, navigation, search,
  and site control panels.
  [tisto]


1.3.7 (2014-10-22)
------------------

- Add upgrade-profile for vs5002 and update rolemap.xml to include
  "Mail forgotten password"-permission also to Managers.
  [ida]

- Added upgrade step for plone.app.querystring which adds new operations and
  fields
  [ichim-david]

- Plone 5 upgrade: Respect previous installed plone.app.event when migrating
  first_weekday setting.
  [thet]

- #12286 Need (Plone 4.0 upgrade) migration step for hidden static text
  portlets
  [anthonygerrard]

- provide upgrade step for plone.protect
  [vangheem]


1.3.6 (2014-03-02)
------------------

- Migrate theme settings, install Barceloneta.
  [davisagli]

- Migrate Members folder default view
  [davisagli]


1.3.5 (2014-02-19)
------------------

- Be sure the improved syndication settings introduced in the 4.3 series
  are applied on upgrade.
  [gbastien]

- Avoid failure at lexicon upgrade (4.3rc1)
  when we have an integrity error into the ZCTextIndex.
  [thomasdesvenain]

- Install plone.app.event and remove portal_calendar when upgarding to Plone 5.
  [davisagli]

- Remove portal_interface when upgrading to Plone 5.
  [ale-rt]

- Remove portal_actionicons, portal_discussion, and portal_undo when
  upgrading to Plone 5.
  [davisagli]

- Add condition to the upgrade step to add scaling-quality 4.3-final.
  plone.app.imaging no longer has the imaging_properties (moved to CMFPlone)
  so they are not there in plone5-tests.
  [pbauer]

- Add conditional install of plonetheme.classic in upgrade step 4.0a1. Since
  plonetheme.classic will be removed in Plone 5, we can not be sure that it
  is always installed.
  [timo]

- Replace deprecated test assert statements.
  [timo]

- Add undeclared Products.TinyMCE dependency.
  [timo]

- Add use_uuid_as_userid site property in Plone 5.
  Part of PLIP 13419.
  [maurits]

- Use lowercase for email login in Plone 5.
  Part of PLIP 13419.
  [maurits]

- Remove persistent kss_mimetype import step.
  [maurits]

- Fix name of Plone 5 zcml conditional feature to plone-5.
  [thet]

- Don't fail on out of date catalog when upgrading syndication for 4.3
  [tomgross]

- Add Default Plone Password Policy to Plone's acl_users.
  [gbastien]

1.3.4 (2013-08-14)
------------------

- Replace basic infrastructure for 4.4 series with same for 5.0 series.
  [davisagli]

- Upgrade TinyMCE: Remove space from style to prevent bogus class.
  [maurits]


1.3.3 (2013-06-13)
------------------

- Add upgrade step to set image scaling quality (p.a.imaging 1.0.8).
  [khink]

- Upgrade broken 'added' content rules.
  [thomasdesvenain]

- handle syndication upgrade when folder is not syndication enabled but
  has syndication information.
  [vangheem]


1.3.2 (2013-05-30)
------------------

- Nothing changed yet.


1.3.1 (2013-04-13)
------------------

- Fix upgrade-step upgradeSyndication for Dexterity
  [pbauer]


1.3 (2013-04-06)
----------------

- Add basic upgrade infrastructure for the Plone 4.4 series.
  [davisagli]

- Do not import Products.kupu. Fixes https://dev.plone.org/ticket/13480
  [danjacka]


1.3rc1 (2013-03-05)
-------------------

- add step for rc1 to upgrade catalog correctly
  [vangheem]

- Avoid hard dependency on ATContentTypes.
  [davisagli]


1.3b2 (2013-01-17)
------------------

- Run plonetheme.sunburst 1.4 upgrade.
  [esteele]

- Add upgrade step for plone.app.discussion.
  [toutpt]


1.3b1 (2013-01-01)
------------------

- Make sure the syndication upgrade step unregisters the old tool
  as a utility.
  [davisagli]

- Add upgrade for version 4.3b1 to make sure TinyMCE is upgraded.
  [davisagli]

- In the UID index migration, if there are items whose key is None,
  skip them instead of complaining about there being multiple items.
  [davisagli]


1.3a2 (2012-10-18)
------------------

- Add upgrade step to remove KSS.
  [vangheem, davisagli]

- Remove old upgrades that depended on KSS being present.
  [davisagli]

- Make sure registry settings for syndication and ResourceRegisties bundles
  are set up for Plone 4.3.
  [vangheem, davisagli]

- Make plone.app.theming upgrade steps only run when plone.app.theming is
  installed (i.e. not for a plain Products.CMFPlone site.)
  [elro]

1.3a1 (2012-08-31)
------------------

- Added Plone 4.3 upgrade step to apply plone.app.jquery 1.5 upgrade step.
  [esteele]

- Added Plone 4.3 upgrade step to re-install plone.app.theming (Diazo theme
  support) if installed previously. This will upgrade the control panel to the
  new unified one.
  [optilude]

- Added Plone 4.3 upgrade step to make sure TinyMCE 1.3 upgrade steps are run.
  [davisagli]

- Added upgrade step for new sortable_title logic.
  [hannosch]

- Add 'displayPublicationDateInByline' property to site properties sheet.
  Required for PLIP #8699.
  [vipod]

- Remove the plone_deprecated skin layer from all skins in Plone 4.3.
  [davisagli]

- Provide kupu tool module alias, so upgrade steps can read data from it.
  [hannosch]

- Remove kupu from the test dependencies.
  [hannosch]

- Make the RAM cache utility upgrade work without zope.app.cache.
  [davisagli]

- Fix an issue in an old upgrade step when used with current
  ResourceRegistries.
  [davisagli]

- Add Member role to View dashboard permission
  [gaudenz]

- Install plone.app.search when upgrading.
  [esteele]

- Plone 4.1.5 upgrade step added that makes sure that plone.app.discussion
  has been properly installed.
  [timo]

1.2.5 (2013-03-05)
------------------

- Add upgrade profile for Plone 4.2.5
  [esteele]


1.2.4 (2013-01-17)
------------------

- Add upgrade profile for Plone 4.2.4
  [esteele]

- Add missing to_423 folder.
  [esteele]


1.2.3 (2012-12-15)
------------------

- Add upgrade profile for Plone 4.2.3
  [esteele]

- In the UID index migration, if there are items whose key is None,
  skip them instead of complaining about there being multiple items.
  [davisagli]


1.2.2 (2012-10-15)
------------------

- Add upgrade step to make sure the registry record for ResourceRegistries
  bundles is installed.
  [davisagli]


1.2.1 (2012-08-11)
------------------

- Add upgrade profile for Plone 4.2.1
  [esteele]


1.2 (2012-06-29)
----------------

- Add upgrade step to install the CMFEditions component registry bases
  modifier.
  [rossp]


1.2rc2 (2012-05-31)
-------------------

- Add profile for Plone 4.2rc2
  [esteele]


1.2rc1 (2012-05-07)
-------------------

- Fix an issue in an old upgrade step when used with current
  ResourceRegistries.
  [davisagli]

- Add Member role to View dashboard permission
  [gaudenz]

- Install plone.app.search when upgrading.
  [esteele]

- Plone 4.1.5 upgrade step added that makes sure that plone.app.discussion
  has been properly installed.
  [timo]


1.2b2 (2012-02-09)
------------------

- Fix adding Site Administrator roles for when
  custom workflows might not have the permission_roles
  for states set.
  [vangheem]


1.2b1 (2011-12-05)
------------------

- Avoid 4020->4100 rules being overpassed from a 4022 version.
  [tdesvenain]

- Add upgrade step to re-enable the getObjPositionInParent index in the
  portal_atcttool.
  [davisagli]

- Add upgrade step to add Site Administrator to allowRolesToAddKeywords.
  [esteele]

1.2a2 - 2011-08-25
------------------

- Release 1.2a2
  [esteele]


1.2a1 - 2011-08-08
------------------

- Removed input-label.js from portal_javascript in the 4.2 alpha profile.
  [spliter]


1.1.7 (2012-06-27)
------------------

- Add Plone 4.1.6 upgrade step.
  [esteele]


1.1.6 (2012-04-18)
------------------

- Add Plone 4.1.5 upgrade step.
  [esteele]


1.1.5 (2012-02-08)
------------------

- Fix adding Site Administrator roles for when
  custom workflows might not have the permission_roles
  for states set.
  [vangheem]


1.1.4 (2011-11-28)
------------------

- Avoid 4020->4100 rules being overpassed from a 4022 version.
  [tdesvenain]


1.1.3 (2011-10-08)
------------------

- Add upgrade step to re-enable the getObjPositionInParent index in the
  portal_atcttool.
  [davisagli]


1.1.2 (2011-09-22)
------------------

- Add missing upgrade steps from recent versions of Plone 4.0.x.
  [davisagli]


1.1.1 (2011-09-21)
------------------

- Fix v41.alphas.convert_to_uuidindex() to truly ignore acquired
  UID values in the index instead of accidentally treating them
  as duplicates, due to a bug in path comparison. Fixes for
  cases where multiple items without UID() method are contained
  in a folder with a UID in a site being upgraded to 4.1:
  http://dev.plone.org/plone/ticket/12185

- Add upgrade step to fix ZCTextIndex OkapiIndex instances with an
  incorrect _totaldoclen
  [davisagli]

- Migrate type icons from content_icon to icon_expr for all FTIs.
  Closes http://dev.plone.org/plone/ticket/12046.
  [thomasdesvenain, vincentfretin]


1.1 - 2011-07-12
----------------

- Fix misnamed metadata.xml files in the 4.1 profiles.
  [esteele]

- Add new upgrade step to add missing UUIDs to Collection-criteria.
  Fixes http://dev.plone.org/plone/ticket/11904.
  [WouterVH]


1.1rc3 - 2011-06-02
-------------------

- In actions.xml, use object_url for the object_buttons.
  Fixes http://dev.plone.org/plone/ticket/11733.
  [WouterVH]

- Actually register the `update_controlpanel_permissions` and
  `update_role_mappings` upgrade steps.
  [hannosch]


1.1rc2 - 2011-05-21
-------------------

- Release 1.1rc2.
  [esteele]


1.1rc1 - 2011-05-20
-------------------

- Adjusted boolean index conversion to new variable index value support
  introduced in ZCatalog 2.13.14.
  [hannosch]

- Added upgrade step to respect the new blacklisted interface list.
  [hannosch]

- Added upgrade step to fix the cataloged ids of interfaces in the
  `object_provides` index. Closes http://dev.plone.org/plone/ticket/11032.
  [hannosch]

- Added new upgrade step to optimize date range index and respect the new
  floor and ceiling date settings.
  [hannosch]

- Removed `v40.alphas.optimizeDateRangeIndexes` upgrade step, as it is
  superseded by the `v41.alphas.optimize_rangeindex` code and would do an
  upgrade that the second step reverted anyways.
  [hannosch]

- Add MANIFEST.in.
  [WouterVH]

- Remove unexistant GenericSetup step dependency on plonepas-content.
  [kiorky]


1.1b2 - 2011-04-06
------------------

- Added a 4.1b2 profile.
  [esteele]


1.1b1 - 2011-03-02
------------------

- Fix handling of BTrees sets when converting the UUIDIndex.
  [rossp]

- Optimize `DateIndex._unindex` internals.
  [hannosch]


1.1a3 - 2011-02-14
------------------

- Upgrade `UID` index to new UUIDIndex.
  [hannosch]

- Upgrade `is_default_page` and `is_folderish` to new boolean index.
  [hannosch]

- Upgrade index internals for field, key and range indexes.
  [hannosch]

- Added 4.1a3 profile.
  [esteele]


1.1a2 - 2011-02-10
------------------

- Added 4.1a2 steps.
  [esteele]


1.1a1 - 2011-01-18
------------------

- Add CMFPlacefulWorkflow, kupu, iterate and p.a.openid to test dependencies
  as the test site zexps contain their objects.
  [elro]

- Make CMFPlacefulWorkflow, kupu and iterate optional during CMFPlone tests.
  [elro]

- Depend on ``Products.CMFPlone`` instead of ``Plone``.
  [elro]

- Added upgrade step to install plone.outputfilters.
  [davisagli]

- Added properties / actions for Single Sign On login form.
  [elro]

- Added upgrade steps to add the Site Administrator role and Site Administrators
  group and update control panel permissions on upgrading to Plone 4.1a1.
  [davisagli]

- Added infrastructure for upgrades to Plone 4.1.
  [davisagli]


1.0.4 - 2011-02-26
------------------

- Add empty profile for 4.0.3-4.0.4 upgrade.
  [esteele]


1.0.3 - 2011-01-18
------------------

- Add empty profile for 4.0.2-4.0.3 upgrade.
  [esteele]


1.0.2 - 2010-11-15
------------------

- During the blob migration of files and images, disable link
  integrity checking, as it can lead to problems, even though no
  content is permanently removed.
  Fixes http://dev.plone.org/plone/ticket/10992
  and   http://dev.plone.org/plone/ticket/11167
  [maurits]


1.0.1 - 2010-09-28
------------------

- Add empty profile for 4.0-4.0.1 upgrade.
  [esteele]

- Avoid relying on the ``Control_Panel/Products`` section, as it is no longer
  used. This closes http://dev.plone.org/plone/ticket/10824.
  [hannosch]


1.0 - 2010-08-28
----------------

- Add empty profile for rc1-final upgrade.
  [esteele]


1.0rc1 - 2010-08-05
-------------------

- Update personal preferences action to its new URL.
  [davisagli]

- Added `padding-left` to the safe_html style whitelist. This refs
  http://dev.plone.org/plone/ticket/10557.
  [hannosch]

- Update license to GPL version 2 only.
  [hannosch]


1.0b5 - 2010-07-07
------------------

- Added upgrade step to remove the ``sunburst_js`` skin layer.
  [hannosch]

- Upgrade step for removing IE8.js from Sunburst.
  [spliter]

- Merged the ``recompilePythonScripts`` upgrade step with the unified folder
  upgrade step. This avoids an extra complete traversal of the entire site.
  [hannosch]

- Rewrote the ``updateIconMetadata`` upgrade step for speed.
  [hannosch]

- Moved the code to remove old persistent Interface records into the
  recompilePythonScripts step. This step actually covers all objects.
  [hannosch]

- Optimized the ``optimizeDateRangeIndexes`` upgrade step to take advantage of
  knowledge about index internals instead of a brute force reindexIndex call.
  [hannosch]

- Optimized the "update getIcon metadata" upgrade step and added a progress
  handler to it.
  [hannosch]

- Enhance the unregisterOldSteps upgrade step, by removing all persistent
  steps for which a ZCML steps exists.
  [hannosch]

- Take a savepoint before starting the unified folder upgrade. This lets us
  fail fast if there's problems pickling anything.
  [hannosch]

- Also catch TypeError's in the action icons upgrade.
  [hannosch]

- Added optional CacheFu uninstallation step. This will remove CacheFu tools
  if they are detected to be broken.
  [hannosch]

- Removing action links from Events, since they are in the template (and were
  never supposed to have actions in the first place). This fixes
  http://dev.plone.org/plone/ticket/10540.
  [limi]

- Re-add the File and Image FTI icon expressions.
  [davisagli]

- Add missing upgrade steps for control panels and site properties.
  Fixes http://dev.plone.org/plone/ticket/10360
  [davisagli]

- Modify the restoreTheme upgrade step to improve handling of themes when
  upgrading from Plone 3. Now if the skin was "Plone Default", it will be
  set to "Plone Classic Theme" if the layers were uncustomized.  If the
  layers were customized, the layers and viewlet settings will be copied to
  a new skin called "Old Plone 3 Custom Theme", and then "Plone Default"
  will be reset to its typical configuration in a fresh Plone 4 site.
  This closes http://dev.plone.org/plone/ticket/10399
  [davisagli]


1.0b4 - 2010-06-03
------------------

- Add ++resource++plone.app.jquerytools.form.js to jsregistry to accomodate
  new jQuery Forms plug in.
  http://dev.plone.org/plone/ticket/10603
  [smcmahon]

- Add upgrade step to convert all files and images to blobs. This closes
  http://dev.plone.org/plone/ticket/10366.
  [hannosch]

- Upgrade the standard File and Image FTI's to use blobs. This refs
  http://dev.plone.org/plone/ticket/10366.
  [hannosch]

- Add upgrade step to remove the Large Plone Folder type for Plone 4.0rc1
  (there is another step which already turns Large Plone Folders into
  unordered regular Folders). Removed references to Large Plone Folder from
  old upgrade steps.
  [davisagli]


1.0b3 - 2010-05-03
------------------

- Added an automated upgrade step to remove old persistent Zope2 Interface
  records. This refs http://dev.plone.org/plone/ticket/10446.
  [dunlapm, hannosch]


1.0b2 - 2010-04-09
------------------

- Add an upgrade step to update the getIcon metadata column for core types so
  that our new CSS sprited icons can be used.
  [esteele]

- Update the safe_html transform with the new config params, migrating existing
  config from Kupu.
  [elro]

- Added upgrade step for viewlet changes in Plone 4.0b2.
  [davisagli]


1.0b1 - 2010-03-08
------------------

- Update the Plone 4 action icons upgrade step to avoid storing icon
  expressions as unicode when possible.
  [davisagli]

- Add step to update viewlet order and hidden managers for the Sunburst theme
  to reflect recent changes.
  [davisagli]

- Add upgrade step to move added recursive_groups plugin to the bottom of the
  IGroupsPlugin list.
  [esteele]

- Added upgrade step to profile version 4007.
  [hannosch]


1.0a5 - 2010-02-19
------------------

- Migrate `getObjPositionInParent` to stub index capable of sorting search
  results according to their position in the container, a.k.a. "nogopip".
  [witsch]

- In migration to 4.0a5, hide the plone.path_bar viewlet from the
  plone.portaltop manager for the Sunburst Theme.
  [davisagli]

- Add new editing control panel.
  [hannosch]

- Removed the no longer needed history viewlet. This refs
  http://dev.plone.org/plone/ticket/10102.
  [hannosch]

- Added upgrade step to update folderish types to add the 'All content'
  folder_full_view. Include IE fixes and disabling of base2 js.
  [elro]

- Add upgrade step to cleanup plonetheme.classic CSS resources upon
  migration. Make plonetheme.classic visible in the QI.
  Refs http://dev.plone.org/plone/ticket/9988.
  [dukebody]

- Added upgrade step to optimize the internal data structures of date range
  indexes as introduced in Zope 2.12.2.
  [hannosch]

- Changed the cleanUpProductRegistry upgrade step to remove all entries from the
  persistent registry and run it again for existing alpha sites.
  [hannosch]


1.0a4 - 2010-02-01
------------------

- Fix theme upgrades by making sure that plone_styles gets updated to
  classic_styles even when it already exists in the skins tool.
  [davisagli]

- Add upgrade step to create, but not install, a recursive groups PAS plugin.
  [esteele]

- Update the `portal_type` of former "Large Folder" content to "Folder".
  Refs http://dev.plone.org/plone/ticket/9791.
  [witsch]

- Make sure the step registry gets cleaned up before the toolset-fixing
  profile gets imported, when upgrading to 4.x.
  [davisagli]

- Add upgrade to pull iefixes from ResourceRegistries.
  Refs http://dev.plone.org/plone/ticket/9278.
  [dukebody]

- Add missing upgrades from Plone 3.3.2 to 3.3.3 to 3.3.4 to 4.0a1.
  [davisagli]

- Call the portal_metadata DCMI upgrade step from CMFDefault when upgrading
  to Plone 4.0b1.
  [davisagli]

- Enable the diff export in functional upgrade tests, we do a complete
  GenericSetup export of all upgraded sites now.
  [hannosch]

- Remove the hint of doing an export/import comparison for the full upgrades.
  These have varying add-ons installed depending on the original site and its
  quite hard to get the same add-ons installed again in a new site.
  [hannosch]

- Added functional upgrade tests based on an actual zexp export of each major
  version of Plone. Each one is imported and upgraded. A diff of the upgraded
  configuration vs the one of a completely new site is generated. Thanks to
  CMF for the inspiration. This closes http://dev.plone.org/plone/ticket/721.
  [hannosch]

- Declared missing dependencies.
  [hannosch]


1.0a3 - 2009-12-16
------------------

- Updated all profile versions in the Plone 4 series to new simple integer
  based numbers.
  [hannosch]

- Updated to match the new profile version for Plone.
  [hannosch]

- Extended the unregisterOldSteps upgrade step to remove persistent step
  registrations now done via ZCML.
  [hannosch]

- Fixed a reference of jquery.js in the Plone 3.0 upgrade steps. The file was
  only introduced in Plone 3.1.
  [hannosch]

- Moved the join action URL expression update to the 4.0a2-4.0a3 step, since
  it never got wired up for a1-a2.
  [davisagli]

- Removed references to content_icon, which is deprecated in CMFCore 2.2.0
  beta 1.
  [davisagli]


1.0a2 - 2009-12-02
------------------

- Provide join_form_fields to user_registration_fields migration.
  [esteele]

- Recompile all persistent Python Scripts during the upgrade.
  [hannosch]

- Simplify installation of new dependencies and include ``plone.app.imaging``.
  [hannosch]

- Run the steps found in the ``Products.CMFPlone:dependencies`` profile.
  [hannosch]

- Remove ``calendarpopup.js`` from portal_javascripts.
  [hannosch]

- Preserve the default theme after an upgrade instead of making sunburst the
  new default. Also ensure the classic_styles layer isn't part of sunburst.
  [hannosch]

- The plone_styles layer is automatically renamed to classic_styles.
  [hannosch]

- Let the mailhost upgrade step replace broken objects with a fresh standard
  mailhost. It's likely our new one has the features of the custom product.
  [hannosch]

- Clean up Zope's product registry to deal with removed products and internal
  changes to the HelpSys catalogs.
  [hannosch]

- Deal with more removed import steps and remove them from the registry.
  [hannosch]

- Cleanup the skins tools and remove broken directory views as well as cleaning
  up the skin selections to avoid references to no longer existing directories.
  [hannosch]

- Remove entries from the toolset registry pointing to no longer existing
  tools. This can happen when add-ons have been uninstalled.
  [hannosch]

- When upgrading to Plone 4.0a1, be sure to update the toolset with new class
  locations before importing any other profiles, which might otherwise fail
  in the toolset step. Be sure to update the locations for the tools which
  moved from CMFPlone to PlonePAS, for upgrades from very old sites.
  [davisagli]


1.0a1 - 2009-11-17
------------------

- Added Products.contentmigration as a dependency.
  [hannosch]

- Fixed removeal of highlightsearchterms.js.
  [naro]

- Added plonetheme.classic and plonetheme.sunburst as dependencies.
  [naro]

- Add migration for unified folders.
  [witsch]

- Replace highlightsearchterms.js with jquery.highlightsearchterms.js
  [mj]

- Add new default modifiers from CMFEditions on upgrade.
  [alecm]

- Adjust the sarissa.js condition on upgrading to Plone 4, so that it doesn't
  break if kupu is absent.
  [davisagli]

- Make sure the TinyMCE profile and default_editor property get installed when
  upgrading to Plone 4 (kupu remains the default editor for upgraded sites).
  [davisagli]

- Aded Migration for SecureMailHost removal
  [alecm]

- Added step to remove the plone_various step from the persistent import
  step registry.
  [davisagli]

- Added upgrade step to remove outdated actions and properties from both the
  Plone Site and TempFolder FTI.
  [hannosch]

- Adjusted setupReferencebrowser upgrade step to proper new-style.
  [hannosch]

- Added property use_email_as_login=False to the site properties in the
  Plone 4 alpha migration. Refs http://dev.plone.org/plone/ticket/9214.
  [maurits]

- Added update of resources to use the authenticated flag instead of a full
  expression where possible, in the Plone 4 alpha migration.
  [davisagli]

- Added renaming of Categories to Tags in the portal_atct tool indices in the
  Plone 4 alpha migration.
  [davisagli]

- Added updating of the actor variable expression for several workflows in the
  Plone 4 alpha migration. This helps fix
  http://dev.plone.org/plone/ticket/7398.
  [davisagli]

- Added removal of action for AT graphviz reference visualization from
  all content types in the Plone 4 alpha migration.
  [davisagli]

- Made the action icons migration switch from GIF to PNG where possible,
  and correctly handle actions in the document_actions category.
  [davisagli]

- Added link to upgrade instructions for sites upgraded from Plone < 2.5
  (technically, sites using GroupUserFolder)
  [davisagli]

- Added a INonInstallable utility to hide this package's profiles from the
  quick installer.
  [davisagli]

- Fixed a couple profiles that were not registered for IMigratingPloneSiteRoot.
  [davisagli]

- Added Plone 4 migration step to add icon_expr to FTIs.
  [davisagli]

- Revert the migration steps for getting rid of the external editor.
  [davisagli]

- Adjusted action icon migration to handle the configlet icons properly.
  [davisagli]

- Re-added missing configlet migrations.
  [davisagli]

- Adjust migration for installing CMFDiffTool to reflect the fact that this is
  now configured in CMFPlone.
  [davisagli]

- Re-add portal_controlpanel to the list of special action providers for the
  migrateOldActions function.
  [davisagli]

- Corrected the migrateActionIcons function to use the correct API for setting
  the new icon_expr, so that the icon_expr_object also gets set correctly.
  [davisagli]

- Adjusted the addMissingWorkflows action to reflect additional variables
  returned by the WorkflowDefinitionConfigurator in current DCWorkflow.
  [davisagli]

- Moved the cleanDefaultCharset action to the 3.0a2-3.0b1 migration; it is a
  prerequisite for that step's properties.xml import.
  [davisagli]

- Adjusted the 2.5-3.0a1 step to correct the toolset registry class metadata
  for the tools which are located in PlonePAS as of Plone 3.
  [davisagli]

- Added migration to make sure we're using an IRAMCache utility from
  zope.ramcache instead of zope.app.cache
  [davisagli]

- Merged changeset 27805 from 3.3 branch migrations for 3.3rc3 to
  3.3rc4 (fix cooked expressions in css registry).
  [maurits]

- Added the z3c.autoinclude entry point so this package is automatically loaded
  on Plone 3.3 and above.
  [hannosch]

- Import the `replace_local_role_manager` method from borg.localrole.
  [hannosch]

- Merge changeset 24257 from 3.2 branch migrations for 3.2 to 3.2.1
  [calvinhp]

- Fixed deprecation warnings for use of Globals.
  [hannosch]

- Specified package dependencies.
  [hannosch]

- Updated method calls to PlonePAS. They lost the out argument.
  [hannosch]

- Adjusted enableZope3Site function to match the new CMF21 upgrade step.
  [hannosch]

- Removed safeGetMemberDataTool method, which wasn't used anywhere.
  [hannosch]

- Initial implementation.
  [hannosch]
