# -*- coding: utf-8 -*-

from imio.migrator.migrator import CURRENTLY_MIGRATING_REQ_VALUE
from imio.migrator.migrator import logger
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
from zope.testing.loggingsupport import InstalledHandler

import logging
import os
import shutil
import tempfile


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

    def _log_handler(self):
        """Capture the imio.migrator log records during the test."""
        handler = InstalledHandler("imio.migrator")
        self.addCleanup(handler.uninstall)
        return handler

    def _link_integrity_enabled(self):
        return api.portal.get_registry_record("plone.enable_link_integrity_checks")

    def test_init(self):
        self.assertEqual(self.migrator.portal, self.portal)
        self.assertTrue(self.portal.REQUEST.get(CURRENTLY_MIGRATING_REQ_VALUE))
        self.assertEqual(self.migrator.warnings, [])
        self.assertFalse(self.migrator.disable_linkintegrity_checks)
        self.assertTrue(self._link_integrity_enabled())
        # the part to run comes from the FUNC_PART environment variable
        with patch.dict(os.environ, {"FUNC_PART": "PART1"}):
            self.assertEqual(Migrator(self.portal).run_part, "PART1")
        with patch.dict(os.environ, {"FUNC_PART": ""}):
            self.assertEqual(Migrator(self.portal).run_part, "")
        # link integrity checks can be disabled during the migration
        migrator = Migrator(self.portal, disable_linkintegrity_checks=True)
        self.assertTrue(migrator.display_mem)
        self.assertTrue(migrator.original_link_integrity)
        self.assertFalse(self._link_integrity_enabled())

    def test_run(self):
        with self.assertRaises(NotImplementedError):
            self.migrator.run()

    def test_is_in_part(self):
        self.migrator.run_part = "RUN_PART"
        self.assertTrue(self.migrator.is_in_part("RUN_PART"))
        self.assertFalse(self.migrator.is_in_part("OTHER_PART"))
        self.migrator.run_part = ""
        self.assertTrue(self.migrator.is_in_part("TEST"))

    def test_log_mem(self):
        handler = self._log_handler()
        self.migrator.log_mem("STEP1")
        self.assertEqual(handler.records, [])
        self.migrator.display_mem = True
        self.migrator.log_mem("STEP1")
        self.assertEqual(len(handler.records), 1)
        message = handler.records[0].getMessage()
        self.assertTrue(message.startswith("Mem used "), message)
        self.assertIn(" at STEP1, (", message)

    def test_warn(self):
        handler = InstalledHandler("my.migration")
        self.addCleanup(handler.uninstall)
        my_logger = logging.getLogger("my.migration")
        self.migrator.warn(my_logger, "Item 1 has no creator")
        self.migrator.warn(my_logger, "Item 2 has no creator")
        self.assertEqual(
            self.migrator.warnings, ["Item 1 has no creator", "Item 2 has no creator"]
        )
        self.assertEqual(
            [(rec.levelname, rec.getMessage()) for rec in handler.records],
            [
                ("WARNING", "Item 1 has no creator"),
                ("WARNING", "Item 2 has no creator"),
            ],
        )

    def test_finish(self):
        handler = self._log_handler()
        self.migrator.finish()
        self.assertFalse(self.portal.REQUEST.get(CURRENTLY_MIGRATING_REQ_VALUE))
        self.assertEqual(self.migrator.warnings, ["No warnings."])
        messages = [rec.getMessage() for rec in handler.records]
        self.assertEqual(
            messages[0],
            "HERE ARE WARNING MESSAGES GENERATED DURING THE MIGRATION : \nNo warnings.",
        )
        self.assertTrue(messages[1].startswith("Migration finished in "))
        # warnings are listed and link integrity checks are restored
        handler.clear()
        migrator = Migrator(self.portal, disable_linkintegrity_checks=True)
        migrator.warn(logger, "Item 1 has no creator")
        migrator.warn(logger, "Item 2 has no creator")
        self.assertFalse(self._link_integrity_enabled())
        migrator.finish()
        self.assertTrue(self._link_integrity_enabled())
        self.assertFalse(self.portal.REQUEST.get(CURRENTLY_MIGRATING_REQ_VALUE))
        self.assertEqual(
            migrator.warnings, ["Item 1 has no creator", "Item 2 has no creator"]
        )
        messages = [rec.getMessage() for rec in handler.records]
        self.assertEqual(
            messages[2],
            "HERE ARE WARNING MESSAGES GENERATED DURING THE MIGRATION : \n"
            "Item 1 has no creator\nItem 2 has no creator",
        )

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
        # an import step whose handler is gone is removed from portal_setup
        self.migrator.ps._import_registry.registerStep(
            "imio.migrator-removed-step",
            handler="imio.migrator.removed_module.import_step",
        )
        metadata = self.migrator.ps.getImportStepMetadata("imio.migrator-removed-step")
        self.assertTrue(metadata["invalid"])
        self.migrator.cleanRegistries(registries=("portal_setup",))
        self.assertIsNone(
            self.migrator.ps.getImportStepMetadata("imio.migrator-removed-step")
        )
        self.assertIn("plone.app.registry", self.migrator.ps.getSortedImportSteps())

    def test_removeUnusedIndexes(self):
        self.catalog.addIndex("old_index", "FieldIndex")
        self.assertIn("old_index", self.catalog.indexes())
        self.migrator.removeUnusedIndexes(indexes=["old_index", "unknown_index"])
        self.assertNotIn("old_index", self.catalog.indexes())
        self.assertIn("Title", self.catalog.indexes())

    def test_removeUnusedColumns(self):
        self.catalog.addColumn("old_column")
        self.assertIn("old_column", self.catalog.schema())
        self.migrator.removeUnusedColumns(columns=["old_column", "unknown_column"])
        self.assertNotIn("old_column", self.catalog.schema())
        self.assertIn("Title", self.catalog.schema())

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
        # filters on portal_types and meta_types; returns True without batching
        self.folder.setTitle("Folder 2")
        self.assertTrue(
            self.migrator.reindexIndexes(update_metadata=True, portal_types=["Folder"])
        )
        self.assertEqual(self.catalog(getId="folder")[0].Title, "Folder 2")
        self.assertEqual(self.catalog(getId="doc")[0].Title, "Fred")
        self.assertTrue(
            self.migrator.reindexIndexes(
                update_metadata=True, meta_types=[self.doc.meta_type]
            )
        )
        self.assertEqual(self.catalog(getId="doc")[0].Title, "Bob")
        # batching: BATCH objects are handled by call, True when all are handled
        self.doc.setTitle("Doc 3")
        batch_dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, batch_dir)
        with patch.dict(os.environ, {"BATCH": "1", "INSTANCE_HOME": batch_dir}):
            self.assertFalse(self.migrator.reindexIndexes(update_metadata=True))
            self.assertTrue(os.listdir(batch_dir))
            self.assertEqual(self.catalog(getId="doc")[0].Title, "Bob")
            for i in range(10):
                if self.migrator.reindexIndexes(update_metadata=True):
                    break
            else:
                self.fail("The batched reindexIndexes never finished")
        self.assertEqual(self.catalog(getId="doc")[0].Title, "Doc 3")
        # batch files are renamed when the batching is finished
        self.assertFalse(
            [name for name in os.listdir(batch_dir) if name.endswith((".pkl", ".txt"))]
        )
        # an object that can't be resolved is logged
        handler = self._log_handler()
        self.folder._delObject("doc", suppress_events=True)
        self.assertEqual(len(self.catalog(getId="doc")), 1)
        self.assertTrue(self.migrator.reindexIndexes(idxs=["Title"]))
        self.assertIn(
            "reindexIndex could not resolve an object from the uid '/plone/folder/doc'.",
            [rec.getMessage() for rec in handler.records],
        )

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
        # the "profile-" prefix is optional, an unknown profile is logged
        handler = self._log_handler()
        ps = self.migrator.ps
        self.assertEqual(
            ps.getLastVersionForProfile("imio.migrator:testing2"), "unknown"
        )
        self.migrator.reinstall(["imio.migrator:testing2", "imio.migrator:unknown"])
        self.assertEqual(
            ps.getLastVersionForProfile("imio.migrator:testing2"), ("1000",)
        )
        self.assertIn(
            "Profile profile-imio.migrator:unknown not found!",
            [rec.getMessage() for rec in handler.records],
        )

    def test_upgradeProfile(self):
        self.migrator.ps.setLastVersionForProfile("imio.migrator:testing", "999")
        info = self.migrator.installer.upgrade_info("imio.migrator")
        self.assertEqual(info["installedVersion"], "999")
        self.migrator.upgradeProfile("imio.migrator:testing")
        info = self.migrator.installer.upgrade_info("imio.migrator")
        self.assertEqual(info["installedVersion"], "1000")
        # a single upgrade step not changing the version itself: the migrator sets it
        ps = self.migrator.ps
        ps.setLastVersionForProfile("imio.migrator:testing2", "999")
        self.migrator.upgradeProfile("imio.migrator:testing2")
        self.assertEqual(
            ps.getLastVersionForProfile("imio.migrator:testing2"), ("1000",)
        )
        # olds: already applied steps with the given destinations are run again
        handler = self._log_handler()
        self.migrator.upgradeProfile("imio.migrator:testing", olds=["2000"])
        self.assertEqual(handler.records, [])
        self.migrator.upgradeProfile("imio.migrator:testing", olds=["1000"])
        self.assertEqual(
            [rec.getMessage() for rec in handler.records],
            [
                "Running upgrade step imio.migrator:testing (999 -> 1000): "
                "Migration step"
            ],
        )
        self.assertEqual(
            ps.getLastVersionForProfile("imio.migrator:testing"), ("1000",)
        )

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
        # the profile being upgraded through the request (profile_id) is omitted
        ps = self.migrator.ps
        ps.setLastVersionForProfile("imio.migrator:testing", "999")
        self.portal.REQUEST.set("profile_id", "imio.migrator:testing")
        self.migrator.upgradeAll(omit=[])
        self.assertEqual(ps.getLastVersionForProfile("imio.migrator:testing"), ("999",))
        # a profile that is not installed is not upgraded
        self.assertEqual(
            ps.getLastVersionForProfile("imio.migrator:testing2"), "unknown"
        )

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
