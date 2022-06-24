Add ``image_scales`` catalog metadata column.
Update all brains to get this info.
Since this takes long on large sites, you can disable this with an environment variable:
``export UPDATE_CATALOG_FOR_IMAGE_SCALES=0``
In that case, you are advised to add the ``image_scales`` column manually to the catalog later.
[maurits]
