Add a commit_threshold for utils.update_catalog_metadata.

Per default it commits every 1000 objects. This should free up some memory for
long running catalog reindexes.

@thet
