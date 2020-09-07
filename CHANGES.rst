Changelog
=========

1.26 (2020-09-07)
-----------------

- Log every 1000 elements instead 100 in `Migrator.reindexIndexes` and
  `Migrator.reindexIndexesFor`.
  [gbastien]

1.25 (2020-08-18)
-----------------

- In `Migrator.removeUnusedPortalTypes`, remove also `portal_types` from
  `site_properties.types_not_searched`.
  [gbastien]

1.24 (2020-06-29)
-----------------

- Fix python 3.8 synthax error.
  [odelaere]


1.23 (2020-05-08)
-----------------

- `ZLogHandler.init` does NOT display a starting message,
  use `ZLogHandler.info` to display initial message so we know
  what we are doing.
  [gbastien]

1.22 (2020-04-29)
-----------------

- Changed `ZLogHandler` steps from 10 to 100 in `reindexIndexesFor` and
  `reindexIndexes` too avoid to fast log scrolling.
  [gbastien]

1.21 (2020-04-23)
-----------------

- Display always warnings at the end of the migration,
  display `No warnings.` if there were not.
  [gbastien]

1.20 (2020-03-12)
-----------------

- Added `migrator.reindexIndexes` method that mimics the Catalog method
  but let's filter `on meta_type/portal_type` and chose to `update_matadata`.
  [gbastien]

1.19 (2020-02-18)
-----------------

- Added logging in `Migrator.reindexIndexesFor`.
  [gbastien]

1.18 (2019-11-25)
-----------------

- Added run_dependencies parameter in runProfileSteps method.
  [sgeulette]

1.17 (2019-10-14)
-----------------

- Add some more logging for actions `Clear and rebuild` or `Refresh` catalog.
  [gbastien]
- Added parameter `catalogsToUpdate` to `refreshDatabase` so we can define what
  catalog will be refreshed because by default, every catalogs are refreshed
  and it is rarely necessary.
  [gbastien]

1.16 (2019-09-12)
-----------------

- Added `Migrator.reindexIndexesFor(idxs=[], **query)` method to be able to
  easily reindex given `idxs` (indexes) on brains returned by
  a given catalog `query`.
  [gbastien]

1.15 (2019-09-12)
-----------------

- Highlight log message about warning messages encountered durung migration.
  [gbastien]
- Fixed `Migrator.refreshDatabase` method, wfs passed to
  `WorkflowTool._recursiveUpdateRoleMappings` need to be a dict with
  `wf id` as `key` and `wf object` as `value`, we had `wf object` for `key`
  and `value`.
  [gbastien]

1.14 (2019-07-19)
-----------------

- Use same format when displaying duration of migration, duration is displayed
  in days/hours/minutes/seconds in any cases.
  [gbastien]

1.13 (2019-06-28)
-----------------

- Be more preceise regarding duration of migration
  (display in seconds and hours/minutes).
  [gbastien]

1.12 (2019-06-14)
-----------------

- Migrator class is no more an old-style class (it inherits from object now).
  [gbastien]

1.11 (2019-05-16)
-----------------

- Added parameter `workflowsToUpdate=[]` to `refreshDatabase` method so when
  parameter `workflows=True`, we may define which workflows to update.
  If nothing defined, every workflows are updated.
  [gbastien]
- Moved methods that disable/restore `enable_link_integrity_checks`
  to `imio.helpers.content`.
  [gbastien]
- Make `portal_workflow` available using `self.wfTool`.
  [gbastien]

1.10 (2019-03-28)
-----------------

- Added a ZLogHandler when updating catalog so some logging showing progression
  is shown in the Zope log.
  [gbastien]
- Set a value in the REQUEST `imio_migrator_currently_migrating` during
  migration so it can be used by other code to know that we are in a migration
  process.
  [gbastien]
- Define `self.catalog` and `self.registry` on base Migrator class so it is
  available for subclasses.
  [gbastien]
- Added method `Migrator.removeUnusedPortalTypes` that will remove
  `portal_types` passed as parameter from tools `portal_types` and
  `portal_factory`.
  [gbastien]
- Requires `imio.helpers`.
  [gbastien]
- Added parameter `disable_linkintegrity_checks=False` to `Migrator.__init__`
  so it is easier to disable linkintegrity checks during a migration.
  Supposed to work with Plone4 and Plone5...
  [gbastien]
- Added install method
  [sgeulette]

1.9 (2019-01-17)
----------------

- Improved and simplified upgradeProfile method
  [sgeulette]

1.8 (2018-10-18)
----------------

- Make REQUEST available thru self.request.
  [gbastien]
- Added methods `removeUnusedColumns` and `removeUnusedIndexes` to easily remove
  columns or indexes from portal_catalog.
  [gbastien]
- Possibility to run specific upgrade steps
  [sgeulette]

1.7 (2018-06-26)
----------------

- Improved reinstall method.
  [sgeulette]
- Improved upgrade step to set directly rigth version.
  [sgeulette]

1.6 (2016-12-07)
----------------

- Added method `warn` that manages warning messages, it will display the warning
  like before in the Zope log but will also store it so every warnings are
  displayed togheter at the end of the migration.
  [gbastien]
- Method `reinstall` may now receive paremeters `ignore_dependencies` and
  `dependency_strategy` to use it when calling `portal_setup.runAllImportStepsFromProfile`.
  This is only useable with Products.GenericSetup >= 1.8.0 (Plone >= 4.3.8).
  [gbastien]

1.5 (2015-11-24)
----------------

- Added method to run given steps of a profile.
  [sgeulette]


1.4 (2015-01-15)
----------------

- Display the catalog we are currently recataloging as several can be recataloged,
  like in version 1.1 but this was lost somehow...
  [gbastien]
- After an upgrade step has been executed, set manually new installed profile version
  or despite upgrade step has been executed, it is still considered not
  [gbastien]

1.3 (2014-10-24)
----------------

- Added methods to run upgrade steps for a given profile or all installed profiles (with pqi update).
  [sgeulette]

1.2 (2014-08-18)
----------------
- Added method to clean registries (portal_javascripts, portal_css and portal_setup)

1.1 (2014-01-30)
----------------
- Display the catalog we are currently recataloging as several can be recataloged
- Prepare release on pypi.imio.be

1.0 (2013-08-20)
----------------
- Manage base migrator, reinstall profiles, refresh catalogs/workflow security, log start/end timestamp
