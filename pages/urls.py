from django.conf.urls.defaults import *
from pages.views import details
from pages import settings

urlpatterns = patterns('',
    # Public pages
    url(r'^$', details, name='pages-root'),
)

if settings.PAGE_USE_ID_IN_URL:
    urlpatterns += patterns('',
        url(r'^.*?(?P<page_id>[0-9]+)/$', details, name='pages-details-by-id'),
    )
else:
    urlpatterns += patterns('',
        url(r'^.*?/?(?P<slug>[-\w]+)/$', details, name='pages-details-by-slug'),
    )
