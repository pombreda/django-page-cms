from os.path import join

# Which template should be used.
PAGES_DEFAULT_TEMPLATE = None

# Could be set to None if you don't need multiple templates.
PAGES_TEMPLATES = ()

# Whether to enable permissions.
PAGES_PERMISSION = True

# Whether to enable tagging. 
PAGES_TAGGING = True

# Whether to only allow unique slugs.
PAGES_UNIQUE_SLUG_REQUIRED = True

# Whether to enable revisions.
PAGES_CONTENT_REVISION = True

# Defines which languages should be offered.
PAGES_LANGUAGES = settings.LANGUAGES

# Defines which language should be used by default and falls back to LANGUAGE_CODE
PAGES_DEFAULT_LANGUAGE = settings.LANGUAGE_CODE[:2]

# Defines how long page content should be cached, including navigation and admin menu.
PAGES_CONTENT_CACHE_DURATION = 60

# You can exclude some placeholder from the revision process
PAGES_CONTENT_REVISION_EXCLUDE_LIST = ()

# Sanitize the user input with html5lib
PAGES_SANITIZE_USER_INPUT = False

# URL that handles pages' media and uses <MEDIA_ROOT>/pages by default.
PAGES_MEDIA_URL = join(settings.MEDIA_URL, 'pages/')

# Show the publication date field in the admin, allows for future dating
# Changing this from True to False could cause some weirdness.  If that is required,
# you should update your database to correct any future dated pages
PAGES_SHOW_START_DATE = False

# Show the publication end date field in the admin, allows for page expiration
# Changing this from True to False could cause some weirdness.  If that is required,
# you should update your database and null any pages with publication_end_date set.
PAGES_SHOW_END_DATE = False
