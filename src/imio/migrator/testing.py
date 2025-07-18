# -*- coding: utf-8 -*-

from plone.app.testing import applyProfile
from plone.app.testing import IntegrationTesting
from plone.app.testing import PLONE_FIXTURE
from plone.app.testing import PloneSandboxLayer

import imio.migrator
import unittest


class ImioMigratorLayer(PloneSandboxLayer):

    defaultBases = (PLONE_FIXTURE,)

    def setUpZope(self, app, configurationContext):
        """Set up Zope."""
        self.loadZCML(package=imio.migrator, name="testing.zcml")

    def setUpPloneSite(self, portal):
        """Set up Plone."""
        portal.portal_workflow.setDefaultChain("simple_publication_workflow")
        applyProfile(portal, "imio.migrator:testing")


FIXTURE = ImioMigratorLayer(name="FIXTURE")
INTEGRATION = IntegrationTesting(bases=(FIXTURE,), name="INTEGRATION")


class IntegrationTestCase(unittest.TestCase):
    """Base class for integration tests."""

    layer = INTEGRATION

    def setUp(self):
        super(IntegrationTestCase, self).setUp()
        self.portal = self.layer["portal"]
