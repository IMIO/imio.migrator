# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# GNU General Public License (GPL)
# ------------------------------------------------------------------------------
'''This module, borrowed from Products.PloneMeeting, defines helper methods to ease
   migration process.'''
# ------------------------------------------------------------------------------
import logging
logger = logging.getLogger('imio.migrator')
import time
from Products.CMFPlone.utils import base_hasattr


class Migrator:
    '''Abstract class for creating a migrator.'''
    def __init__(self, context):
        self.context = context
        self.portal = context.portal_url.getPortalObject()
        self.startTime = time.time()

    def run(self):
        '''Must be overridden. This method does the migration job.'''
        raise 'You should have overridden me darling.'''

    def finish(self):
        '''At the end of the migration, you can call this method to log its
           duration in minutes.'''
        seconds = time.time() - self.startTime
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
            logger.info('Recataloging...')
            # Manage the catalogs we want to clear and rebuild
            # We have to call another method as clear=1 passed to refreshCatalog
            #does not seem to work as expected...
            for catalog in catalogsToRebuild:
                catalogObj = getattr(self.portal, catalog)
                if base_hasattr(catalogObj, 'clearFindAndRebuild'):
                    catalogObj.clearFindAndRebuild()
                else:
                    # special case for the uid_catalog
                    catalogObj.manage_rebuildCatalog()
            catalogIds = ('portal_catalog', 'reference_catalog', 'uid_catalog')
            for catalogId in catalogIds:
                if not catalogId in catalogsToRebuild:
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
            setuptool = self.portal.portal_setup
            for stepId in setuptool.getSortedImportSteps():
                stepMetadata = setuptool.getImportStepMetadata(stepId)
                # remove invalid steps
                if stepMetadata['invalid']:
                    logger.info('Removing %s step from portal_setup' % stepId)
                    setuptool._import_registry.unregisterStep(stepId)
            logger.info('portal_setup has been cleaned!')
        logger.info('Registries have been cleaned!')

    def reinstall(self, profiles):
        '''Allows to reinstall a series of p_profiles.'''
        logger.info('Reinstalling product(s) %s...' % ', '.join([profile[8:] for profile in profiles]))
        for profile in profiles:
            try:
                self.portal.portal_setup.runAllImportStepsFromProfile(profile)
            except KeyError:
                logger.error('Profile %s not found!' % profile)
        logger.info('Done.')
