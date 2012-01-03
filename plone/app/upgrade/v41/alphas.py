import logging

import transaction
from BTrees.IIBTree import IIBTree
from BTrees.IIBTree import IISet
from BTrees.IIBTree import IITreeSet
from BTrees.OIBTree import OIBTree
from BTrees.Length import Length
from Products.CMFCore.utils import getToolByName
from Products.GenericSetup.rolemap import RolemapExportConfigurator
from Products.PluginIndexes.BooleanIndex.BooleanIndex import BooleanIndex
from Products.PluginIndexes.DateIndex.DateIndex import DateIndex
from Products.PluginIndexes.FieldIndex.FieldIndex import FieldIndex
from Products.PluginIndexes.KeywordIndex.KeywordIndex import KeywordIndex
from Products.PluginIndexes.UUIDIndex.UUIDIndex import UUIDIndex

from plone.app.upgrade.utils import loadMigrationProfile

logger = logging.getLogger('plone.app.upgrade')


def to41alpha1(context):
    loadMigrationProfile(context, 'profile-plone.app.upgrade.v41:to41alpha1')

def add_siteadmin_role(context):
    portal = getToolByName(context, 'portal_url').getPortalObject()

    # add the role to the site
    immediate_roles = list( getattr(portal, '__ac_roles__', []) )
    if 'Site Administrator' not in immediate_roles:
        immediate_roles.append('Site Administrator')
        immediate_roles.sort()
        portal.__ac_roles__ = tuple(immediate_roles)

    # add the Site Administrators group
    uf = getToolByName(context, 'acl_users')
    gtool = getToolByName(context, 'portal_groups')
    if not uf.searchGroups(id='Site Administrators'):
        gtool.addGroup('Site Administrators', title='Site Administrators', roles=['Site Administrator'])

    # update rolemap:
    # add Site Administrator role to permissions that have the Manager role,
    # plus some additional ones that only have Manager as a default role
    rolemap_exporter = RolemapExportConfigurator(portal)
    permissions = rolemap_exporter.listPermissions()
    extra_permissions = set([
        'Access arbitrary user session data',
        'Access contents information',
        'Access inactive portal content',
        'Access session data',
        'Add portal content',
        'Add portal events',
        'Change local roles',
        'Change portal events',
        'Copy or Move',
        'Mail forgotten password',
        'Modify portal content',
        'Review portal content',
        'Search ZCatalog',
        'Use Database Methods',
        'Use mailhost services',
        'Use version control',
        'View',
        'View History',
        'WebDAV Lock items',
        'WebDAV Unlock items',
        'WebDAV access',
        ])
    try:
        import Products.kupu
    except ImportError:
        pass
    else:
        extra_permissions.update([
        'Kupu: Manage libraries',
        'Kupu: Query libraries',
        ])
    exclude_permissions = set([
        'Manage portal',
        'View management screens',
        ])
    for permission_info in permissions:
        if permission_info['name'] in exclude_permissions:
            continue
        is_extra = permission_info['name'] in extra_permissions
        if is_extra:
            extra_permissions.remove(permission_info['name'])
        if is_extra or 'Manager' in permission_info['roles']:
            roles = permission_info['roles']
            roles.append('Site Administrator')
            roles.sort()
            portal.manage_permission(permission_info['name'],
                                     roles,
                                     permission_info['acquire'])
    for permission_id in extra_permissions:
        portal.manage_permission(permission_id, ['Site Administrator',], True)

    # update workflows:
    # add Site Administrator role where Manager already is;
    wtool = getToolByName(portal, 'portal_workflow')
    for workflow_id in wtool.getWorkflowIds():
        workflow = wtool[workflow_id]
        for state_id in workflow.states:
            state = workflow.states[state_id]
            if state.permission_roles is None:
                continue
            for permission_id, roles in state.permission_roles.items():
                if 'Manager' in roles:
                    new_roles = list(roles)
                    new_roles.append('Site Administrator')
                    state.setPermission(permission_id, isinstance(roles, list), new_roles)

def update_role_mappings(context):
    wtool = getToolByName(context, 'portal_workflow')
    wtool.updateRoleMappings()

def update_controlpanel_permissions(context):
    cptool = getToolByName(context, 'portal_controlpanel')

    new_permissions = {
        'PloneReconfig': 'Plone Site Setup: Site',
        'UsersGroups': 'Plone Site Setup: Users and Groups',
        'UsersGroups2': 'Plone Site Setup: Users and Groups',
        'MailHost': 'Plone Site Setup: Mail',
        'PortalSkin': 'Plone Site Setup: Themes',
        'EditingSettings': 'Plone Site Setup: Editing',
        'TypesSettings': 'Plone Site Setup: Types',
        'MarkupSettings': 'Plone Site Setup: Markup',
        'SecuritySettings': 'Plone Site Setup: Security',
        'SearchSettings': 'Plone Site Setup: Search',
        'NavigationSettings': 'Plone Site Setup: Navigation',
        'PloneLanguageTool': 'Plone Site Setup: Language',
        'CalendarSettings': 'Plone Site Setup: Calendar',
        'HtmlFilter': 'Plone Site Setup: Filtering',
        'tinymce': 'Plone Site Setup: TinyMCE',
        'ImagingSettings': 'Plone Site Setup: Imaging',
    }

    for action in cptool._actions:
        if action.id in new_permissions:
            action.permissions = (new_permissions[action.id], )

def install_outputfilters(context):
    qi = getToolByName(context, 'portal_quickinstaller')
    if qi.isProductInstallable('plone.outputfilters'):
        if not qi.isProductInstalled('plone.outputfilters'):
            qi.installProduct('plone.outputfilters')


def to41alpha2(context):
    loadMigrationProfile(context, 'profile-plone.app.upgrade.v41:to41alpha2')


def convert_to_booleanindex(catalog, index):
    if isinstance(index, BooleanIndex):
        return
    logger.info('Converting index `%s` to BooleanIndex.' % index.getId())
    index.__class__ = BooleanIndex
    index._p_changed = True
    catalog._catalog._p_changed = True

    # convert _unindex from IOBTree to IIBTree
    sets = {0: IITreeSet(), 1: IITreeSet()}
    old_unindex = index._unindex
    index._unindex = _unindex = IIBTree()
    for k, v in old_unindex.items():
        # docid to value (True, False)
        value = int(bool(v))
        _unindex[k] = value
        sets[value].add(k)
    del old_unindex

    # convert _index from OOBTree to IITreeSet and set lengths
    false_length = len(sets[0])
    true_length = len(sets[1])
    index._length = Length(false_length + true_length)
    # we put the smaller set into the index
    if false_length < true_length:
        index._index_value = 0
        index._index_length = Length(false_length)
        index._index = sets[0]
        del sets[1]
    else:
        index._index_value = 1
        index._index_length = Length(true_length)
        index._index = sets[1]
        del sets[0]
    transaction.savepoint(optimistic=True)
    logger.info('Finished conversion.')


def convert_to_uuidindex(catalog, index):
    if isinstance(index, UUIDIndex):
        return
    logger.info('Converting index `%s` to UUIDIndex.' % index.getId())
    index.__class__ = UUIDIndex
    index._p_changed = True
    catalog._catalog._p_changed = True
    # convert from OOBTree to OIBTree
    old_index = index._index
    if not isinstance(old_index, OIBTree):
        index._index = _index = OIBTree()
        for k, v in old_index.items():
            if isinstance(v, int):
                _index[k] = v
            else:
                if isinstance(v, (IISet, IITreeSet)):
                    # inconsistent data, one uid with multiple docids
                    paths = dict((tuple(catalog.getpath(k).split('/')), k)
                                 for k in v.keys())
                    shortest = min(paths, key=len)
                    for path, key in paths.iteritems():
                        if path[:len(shortest)] != shortest:
                            raise ValueError(
                                'Inconsistent UID index, UID %s is associated '
                                'with multiple docids: %r' % (k, paths))

                    # All other docids are sub-paths of another
                    # indicating the UID was just acquired,
                    # choose the shortest
                    _index[k] = paths[shortest]
        del old_index
        transaction.savepoint(optimistic=True)
    logger.info('Finished conversion.')


def optimize_dateindex(index):
    # migrate _unindex from OIBTree to IIBTree
    old_unindex = index._unindex
    if isinstance(old_unindex, IIBTree):
        return
    index._unindex = _unindex = IIBTree()
    logger.info('Converting to IIBTree for index `%s`.' % index.getId())
    for pos, (k, v) in enumerate(old_unindex.items()):
        _unindex[k] = v
        if pos and pos % 10000 == 0:
            transaction.savepoint(optimistic=True)
            logger.info('Processed %s items.' % pos)

    transaction.savepoint(optimistic=True)
    logger.info('Finished conversion.')


def optimize_unindex(index):
    # avoid using a simple int and always use a treeset instead to
    # allow conflict resolution inside the treeset to happen
    _index = getattr(index, '_index', None)
    if _index is not None:
        logger.info('Converting to IITreeSet for index `%s`.' % index.getId())
        i = 0
        for k, v in enumerate(_index.items()):
            if isinstance(v, int):
                _index[k] = IITreeSet((v, ))
                i += 1
                if i % 10000 == 0:
                    transaction.savepoint(optimistic=True)
                    logger.info('Processed %s items.' % i)
        transaction.savepoint(optimistic=True)
        logger.info('Finished conversion.')


def optimize_indexes(context):
    catalog = getToolByName(context, 'portal_catalog')
    for index in catalog.getIndexObjects():
        index_id = index.getId()
        if isinstance(index, DateIndex):
            optimize_dateindex(index)
        elif index_id in ('is_default_page', 'is_folderish'):
            convert_to_booleanindex(catalog, index)
        elif index_id == 'UID':
            convert_to_uuidindex(catalog, index)
        elif isinstance(index, (FieldIndex, KeywordIndex)):
            optimize_unindex(index)


def to41alpha3(context):
    loadMigrationProfile(context, 'profile-plone.app.upgrade.v41:to41alpha3')
    optimize_indexes(context)
