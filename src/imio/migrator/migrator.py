# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# GNU General Public License (GPL)
# ------------------------------------------------------------------------------
'''This module, borrowed from Products.PloneMeeting, defines helper methods
   to ease migration process.'''
# ------------------------------------------------------------------------------
import logging
import time
from Products.CMFPlone.utils import base_hasattr

logger = logging.getLogger('imio.migrator')


class Migrator:
    '''Abstract class for creating a migrator.'''
    def __init__(self, context):
        self.context = context
        self.portal = context.portal_url.getPortalObject()
        self.ps = self.portal.portal_setup
        self.startTime = time.time()
        self.warnings = []

    def run(self):
        '''Must be overridden. This method does the migration job.'''
        raise 'You should have overridden me darling.'

    def warn(self, logger, warning_msg):
        '''Manage warning messages, into logger and saved into self.warnings.'''
        logger.warn(warning_msg)
        self.warnings.append(warning_msg)

    def finish(self):
        '''At the end of the migration, you can call this method to log its
           duration in minutes.'''
        seconds = time.time() - self.startTime
        if self.warnings:
            logger.info('Here are warning messages generated during the migration : \n{0}'.format(
                '\n'.join(self.warnings))
            )
        logger.info('Migration finished in %d minute(s).' % (seconds/60))

    def refreshDatabase(self,
                        catalogs=True,
                        catalogsToRebuild=['portal_catalog'],
                        workflows=False):
        '''After the migration script has been executed, it can be necessary to
           update the Plone catalogs and/or the workflow settings on every
           database object if workflow definitions have changed. We can pass
           catalog ids we want to 'clear and rebuild' using
           p_catalogsToRebuild.'''
        if catalogs:
            # Manage the catalogs we want to clear and rebuild
            # We have to call another method as clear=1 passed to refreshCatalog
            # does not seem to work as expected...
            for catalog in catalogsToRebuild:
                logger.info('Recataloging %s...' % catalog)
                catalogObj = getattr(self.portal, catalog)
                if base_hasattr(catalogObj, 'clearFindAndRebuild'):
                    catalogObj.clearFindAndRebuild()
                else:
                    # special case for the uid_catalog
                    catalogObj.manage_rebuildCatalog()
            catalogIds = ('portal_catalog', 'reference_catalog', 'uid_catalog')
            for catalogId in catalogIds:
                if catalogId not in catalogsToRebuild:
                    catalogObj = getattr(self.portal, catalogId)
                    catalogObj.refreshCatalog(clear=0)
        if workflows:
            logger.info('Refresh workflow-related information on every object of the database...')
            self.portal.portal_workflow.updateRoleMappings()

    def cleanRegistries(self, registries=('portal_javascripts', 'portal_css', 'portal_setup')):
        '''
          Clean p_registries, remove not found elements.
        '''
        logger.info('Cleaning registries...')
        if 'portal_javascripts' in registries:
            jstool = self.portal.portal_javascripts
            for script in jstool.getResources():
                scriptId = script.getId()
                resourceExists = script.isExternal or self.portal.restrictedTraverse(scriptId, False) and True
                if not resourceExists:
                    # we found a notFound resource, remove it
                    logger.info('Removing %s from portal_javascripts' % scriptId)
                    jstool.unregisterResource(scriptId)
            jstool.cookResources()
            logger.info('portal_javascripts has been cleaned!')

        if 'portal_css' in registries:
            csstool = self.portal.portal_css
            for sheet in csstool.getResources():
                sheetId = sheet.getId()
                resourceExists = sheet.isExternal or self.portal.restrictedTraverse(sheetId, False) and True
                if not resourceExists:
                    # we found a notFound resource, remove it
                    logger.info('Removing %s from portal_css' % sheetId)
                    csstool.unregisterResource(sheetId)
            csstool.cookResources()
            logger.info('portal_css has been cleaned!')

        if 'portal_setup' in registries:
            # clean portal_setup
            for stepId in self.ps.getSortedImportSteps():
                stepMetadata = self.ps.getImportStepMetadata(stepId)
                # remove invalid steps
                if stepMetadata['invalid']:
                    logger.info('Removing %s step from portal_setup' % stepId)
                    self.ps._import_registry.unregisterStep(stepId)
            logger.info('portal_setup has been cleaned!')
        logger.info('Registries have been cleaned!')

    def reinstall(self, profiles, ignore_dependencies=False, dependency_strategy=None):
        '''Allows to reinstall a series of p_profiles.'''
        logger.info('Reinstalling product(s) %s...' % ', '.join([profile.startswith('profile-') and profile[8:] or
                                                                 profile for profile in profiles]))
        for profile in profiles:
            if not profile.startswith('profile-'):
                profile = 'profile-%s' % profile
            try:
                self.ps.runAllImportStepsFromProfile(profile,
                                                     ignore_dependencies=ignore_dependencies,
                                                     dependency_strategy=dependency_strategy)
            except KeyError:
                logger.error('Profile %s not found!' % profile)
        logger.info('Done.')

    def upgradeProfile(self, profile):
        """ Get upgrade step and run it """

        def run_upgrade_step(step, source, dest, last_flag):
            logger.info('Running upgrade step %s (%s -> %s): %s' % (profile, source, dest, step.title))
            step.doStep(self.ps)
            self.ps.setLastVersionForProfile(profile, dest)
            # we update portal_quickinstaller if the current step is the last one
            if last_flag:
                pqi = self.portal.portal_quickinstaller
                try:
                    product = profile.split(':')[0]
                    prod = pqi.get(product)
                    setattr(prod, 'installedversion', pqi.getProductVersion(product))
                except IndexError, e:
                    logger.error("Cannot extract product from profile '%s': %s" % (profile, e))
                except AttributeError, e:
                    logger.error("Cannot get product '%s' from portal_quickinstaller: %s" % (product, e))

        upgrades = self.ps.listUpgrades(profile)
        last_i = len(upgrades)-1
        for i, container in enumerate(upgrades):
            last_flag = False
            if isinstance(container, dict):
                if i == last_i:
                    last_flag = True
                run_upgrade_step(container['step'], container['ssource'], container['sdest'], last_flag)
            elif isinstance(container, list):
                last_j = len(container)-1
                for j, dic in enumerate(container):
                    if i == last_i and j == last_j:
                        last_flag = True
                    run_upgrade_step(dic['step'], dic['ssource'], dic['sdest'], last_flag)

    def upgradeAll(self, omit=[]):
        """ Upgrade all upgrade profiles except those in omit parameter list """
        if self.portal.REQUEST.get('profile_id'):
            omit.append(self.portal.REQUEST.get('profile_id'))
        for profile in self.ps.listProfilesWithUpgrades():
            # make sure the profile isn't the current (or must be avoided) and
            # the profile is well installed
            if profile not in omit and self.ps.getLastVersionForProfile(profile) != 'unknown':
                self.upgradeProfile(profile)

    def runProfileSteps(self, product, steps=[], profile='default'):
        """ Run given steps of a product profile (default is 'default' profile) """
        for step_id in steps:
            logger.info("Running profile step '%s:%s' => %s" % (product, profile, step_id))
            self.ps.runImportStepFromProfile('profile-%s:%s' % (product, profile), step_id)
