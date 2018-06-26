Changelog
=========

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
