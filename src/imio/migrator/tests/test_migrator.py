# -*- coding: utf-8 -*-

from imio.migrator.migrator import Migrator
from imio.migrator.testing import IntegrationTestCase
from plone import api
from plone.app.testing import login
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID
from plone.app.testing import TEST_USER_NAME
from plone.base.interfaces import IBundleRegistry
from Products.CMFCore.indexing import processQueue
from Products.CMFCore.permissions import AccessContentsInformation
from Products.CMFCore.permissions import View
from Products.CMFCore.utils import _checkPermission
from unittest.mock import patch


class TestMigrator(IntegrationTestCase):

    def setUp(self):
        self.portal = self.layer["portal"]
        self.catalog = api.portal.get_tool("portal_catalog")
        self.wf_tool = api.portal.get_tool("portal_workflow")
        setRoles(self.portal, TEST_USER_ID, ["Manager"])
        self.folder = api.content.create(
            container=self.portal,
            type="Folder",
            title="Folder",
            id="folder",
        )
        self.doc = api.content.create(
            container=self.folder,
            type="Document",
            id="doc",
            title="Foo",
            description="Bar",
        )
        self.migrator = Migrator(self.portal)
        self.migrator.display_mem = False
        processQueue()

    def test_run(self):
        with self.assertRaises(NotImplementedError):
            self.migrator.run()

    def test_is_in_part(self):
        self.migrator.run_part = "RUN_PART"
        self.assertTrue(self.migrator.is_in_part("RUN_PART"))
        self.assertFalse(self.migrator.is_in_part("OTHER_PART"))
        self.migrator.run_part = ""
        self.assertTrue(self.migrator.is_in_part("TEST"))

    def test_refreshDatabase(self):
        self.catalog.unindexObject(self.folder.doc)
        self.assertEqual(len(self.catalog(getId="doc")), 0)
        self.migrator.refreshDatabase(
            catalogs=True,
            catalogsToRebuild=[],
            catalogsToUpdate=[],
        )
        self.assertEqual(len(self.catalog(getId="doc")), 0)
        self.migrator.refreshDatabase(catalogs=False)
        self.assertEqual(len(self.catalog(getId="doc")), 0)
        self.migrator.refreshDatabase(catalogs=True)
        self.assertEqual(len(self.catalog(getId="doc")), 1)
        self.catalog.unindexObject(self.folder.doc)
        self.assertEqual(len(self.catalog(getId="doc")), 0)
        self.migrator.refreshDatabase(
            catalogs=True,
            catalogsToRebuild=[],
            catalogsToUpdate=["portal_catalog"],
        )
        self.assertEqual(len(self.catalog(getId="doc")), 0)
        self.catalog.reindexObject(self.folder.doc)
        self.assertEqual(len(self.catalog(getId="doc")), 1)
        self.folder.doc.setTitle("Fred")
        self.folder.doc.setDescription("BamBam")
        self.migrator.refreshDatabase(
            catalogs=True,
            catalogsToRebuild=[],
            catalogsToUpdate=["portal_catalog"],
        )
        brain = self.catalog(getId="doc")[0]
        self.assertEqual(brain.getId, "doc")
        self.assertEqual(brain.Title, "Fred")
        self.assertEqual(brain.Description, "BamBam")
        self.catalog.unindexObject(self.folder.doc)
        self.assertEqual(len(self.catalog(getId="doc")), 0)
        self.migrator.refreshDatabase(
            catalogs=True,
            catalogsToRebuild=["portal_catalog"],
            catalogsToUpdate=[],
        )
        self.assertEqual(len(self.catalog(getId="doc")), 1)
        self.assertTrue(_checkPermission(View, self.doc))
        self.assertEqual(len(self.catalog(getId="doc")), 1)
        wf = self.portal.portal_workflow.getWorkflowsFor(self.doc)[0]
        wf.states.private.permission_roles[AccessContentsInformation] = ("Manager",)
        wf.states.private.permission_roles[View] = ("Manager",)
        setRoles(self.portal, TEST_USER_ID, ["Member"])
        login(self.portal, TEST_USER_NAME)
        self.assertTrue(_checkPermission(View, self.doc))
        self.assertEqual(len(self.catalog(getId="doc")), 1)
        self.migrator.refreshDatabase(
            catalogs=False,
            workflows=True,
        )
        self.assertFalse(_checkPermission(View, self.doc))
        self.assertEqual(len(self.catalog(getId="doc")), 0)
        wf.states.private.permission_roles[AccessContentsInformation] = ("Member",)
        wf.states.private.permission_roles[View] = ("Member",)
        self.migrator.refreshDatabase(
            catalogs=False,
            workflows=True,
            workflowsToUpdate=["simple_publication_workflow"],
        )
        self.assertTrue(_checkPermission(View, self.doc))
        self.assertEqual(len(self.catalog(getId="doc")), 1)

    def test_cleanRegistries(self):
        bundles = self.migrator.registry.collectionOfInterface(
            IBundleRegistry, prefix="plone.bundles", check=False
        )
        self.assertTrue("broken-css-bundle" in bundles.keys())
        self.assertTrue("broken-js-bundle" in bundles.keys())
        self.migrator.cleanRegistries()
        bundles = self.migrator.registry.collectionOfInterface(
            IBundleRegistry, prefix="plone.bundles", check=False
        )
        self.assertFalse("broken-css-bundle" in bundles.keys())
        self.assertFalse("broken-js-bundle" in bundles.keys())

    def test_removeUnusedPortalTypes(self):
        self.assertIn("TempFolder", self.migrator.portal.portal_types)
        self.assertIn(
            "TempFolder", self.migrator.registry.get("plone.types_not_searched")
        )
        self.migrator.removeUnusedPortalTypes(["TempFolder"])
        self.assertNotIn("TempFolder", self.migrator.portal.portal_types)
        self.assertNotIn(
            "TempFolder", self.migrator.registry.get("plone.types_not_searched")
        )

    def test_clean_orphan_brains(self):
        self.assertEqual(len(self.catalog(getId="doc")), 1)
        with patch(
            "Products.ZCatalog.CatalogBrains.AbstractCatalogBrain.getObject",
            side_effect=AttributeError,
        ):
            self.migrator.clean_orphan_brains({})
        self.assertEqual(len(self.catalog(getId="doc")), 0)

    def test_reindexIndexes(self):
        self.folder.doc.setTitle("Fred")
        self.folder.doc.setDescription("BamBam")
        self.migrator.reindexIndexes(idxs=["Title"], update_metadata=True)
        brain = self.catalog(getId="doc")[0]
        self.assertEqual(brain.getId, "doc")
        self.assertEqual(brain.Title, "Fred")
        self.assertEqual(brain.Description, "BamBam")
        self.folder.doc.setTitle("Bob")
        self.folder.doc.setDescription("BimBim")
        self.migrator.reindexIndexes(idxs=["Title"], update_metadata=False)
        brain = self.catalog(getId="doc")[0]
        self.assertEqual(brain.getId, "doc")
        self.assertEqual(brain.Title, "Fred")
        self.assertEqual(brain.Description, "BamBam")

    def test_reindexIndexesFor(self):
        self.folder.doc.setTitle("Fred")
        self.folder.doc.setDescription("BamBam")
        self.migrator.reindexIndexesFor(idxs=["Title"], portal_type=["Folder"])
        brain = self.catalog(getId="doc")[0]
        self.assertEqual(brain.getId, "doc")
        self.assertEqual(brain.Title, "Foo")
        self.assertEqual(brain.Description, "Bar")
        self.migrator.reindexIndexesFor(idxs=["Title"], portal_type=["Document"])
        brain = self.catalog(getId="doc")[0]
        self.assertEqual(brain.getId, "doc")
        self.assertEqual(brain.Title, "Fred")
        self.assertEqual(brain.Description, "BamBam")

    def test_install(self):
        self.assertFalse(self.migrator.installer.is_product_installed("plone.session"))
        self.migrator.install(["plone.session"])
        self.assertTrue(self.migrator.installer.is_product_installed("plone.session"))

    def test_reinstall(self):
        self.assertFalse(self.migrator.installer.is_product_installed("plone.session"))
        self.migrator.install(["plone.session"])
        self.migrator.reinstall(["profile-plone.session:default"])
        self.assertTrue(self.migrator.installer.is_product_installed("plone.session"))
        self.migrator.installer.uninstall_product("plone.session")
        self.migrator.reinstall(["profile-plone.session:default"])
        self.assertTrue(self.migrator.installer.is_product_installed("plone.session"))

    def test_upgradeProfile(self):
        self.migrator.ps.setLastVersionForProfile("imio.migrator:testing", "999")
        info = self.migrator.installer.upgrade_info("imio.migrator")
        self.assertEqual(info["installedVersion"], "999")
        self.migrator.upgradeProfile("imio.migrator:testing")
        info = self.migrator.installer.upgrade_info("imio.migrator")
        self.assertEqual(info["installedVersion"], "1000")

    def test_upgradeAll(self):
        self.migrator.ps.setLastVersionForProfile("imio.migrator:testing", "999")
        info = self.migrator.installer.upgrade_info("imio.migrator")
        self.assertEqual(info["installedVersion"], "999")
        self.migrator.upgradeAll(omit=["imio.migrator:testing"])
        info = self.migrator.installer.upgrade_info("imio.migrator")
        self.assertEqual(info["installedVersion"], "999")
        self.migrator.upgradeAll()
        info = self.migrator.installer.upgrade_info("imio.migrator")
        self.assertEqual(info["installedVersion"], "1000")

    def test_runProfileSteps(self):
        bundles = self.migrator.registry.collectionOfInterface(
            IBundleRegistry, prefix="plone.bundles", check=False
        )
        self.assertFalse("my-bundle" in bundles.keys())
        self.migrator.runProfileSteps(
            "imio.migrator",
            steps=["plone.app.registry"],
            profile="testing2",
            run_dependencies=False,
        )
        bundles = self.migrator.registry.collectionOfInterface(
            IBundleRegistry, prefix="plone.bundles", check=False
        )
        self.assertTrue("my-bundle" in bundles.keys())
