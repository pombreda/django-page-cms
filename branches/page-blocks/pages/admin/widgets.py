from os.path import join
from django.forms import TextInput, Textarea
from django.utils.safestring import mark_safe
from django.template import RequestContext
from django.template.loader import render_to_string

from pages.conf import settings
from pages.models import Page, tagging

if tagging:
    from tagging.models import Tag
    from django.utils import simplejson

    class AutoCompleteTagInput(TextInput):
        class Media:
            js = [join(settings.PAGES_MEDIA_URL, path) for path in (
                'javascript/jquery.js',
                'javascript/jquery.bgiframe.min.js',
                'javascript/jquery.ajaxQueue.js',
                'javascript/jquery.autocomplete.min.js'
            )]

        def render(self, name, value, attrs=None):
            rendered = super(AutoCompleteTagInput, self).render(name, value, attrs)
            page_tags = Tag.objects.usage_for_model(Page)
            context = {
                'name': name,
                'tags': simplejson.dumps([tag.name for tag in page_tags], ensure_ascii=False),
            }
            return rendered + mark_safe(render_to_string(
                'admin/pages/page/widgets/autocompletetaginput.html', context))

class RichTextarea(Textarea):
    class Media:
        js = [join(settings.PAGES_MEDIA_URL, path) for path in (
            'javascript/jquery.js',
        )]
        css = {
            'all': [join(settings.PAGES_MEDIA_URL, path) for path in (
                'css/rte.css',
            )]
        }

    def __init__(self, attrs=None):
        attrs = {'class': 'rte'}
        super(RichTextarea, self).__init__(attrs)

    def render(self, name, value, attrs=None):
        rendered = super(RichTextarea, self).render(name, value, attrs)
        context = {
            'name': name,
            'settings.PAGES_MEDIA_URL': settings.PAGES_MEDIA_URL,
        }
        return rendered + mark_safe(render_to_string(
            'admin/pages/page/widgets/richtextarea.html', context))

class WYMEditor(Textarea):
    class Media:
        js = [join(settings.PAGES_MEDIA_URL, path) for path in (
            'javascript/jquery.js',
            'wymeditor/jquery.wymeditor.js',
            'wymeditor/plugins/resizable/jquery.wymeditor.resizable.js',
        )]

    def __init__(self, language=None, attrs=None):
        self.language = language or settings.LANGUAGE_CODE[:2]
        self.attrs = {'class': 'wymeditor'}
        if attrs:
            self.attrs.update(attrs)
        super(WYMEditor, self).__init__(attrs)

    def render(self, name, value, attrs=None):
        rendered = super(WYMEditor, self).render(name, value, attrs)
        context = {
            'name': name,
            'language': self.language,
            'settings.PAGES_MEDIA_URL': settings.PAGES_MEDIA_URL,
        }
        return rendered + mark_safe(render_to_string(
            'admin/pages/page/widgets/wymeditor.html', context))

class markItUpMarkdown(Textarea):
    class Media:
        js = [join(settings.PAGES_MEDIA_URL, path) for path in (
            'javascript/jquery.js',
            'markitup/jquery.markitup.js',
            'markitup/sets/markdown/set.js',
        )]
        css = {
            'all': [join(settings.PAGES_MEDIA_URL, path) for path in (
                'markitup/skins/simple/style.css',
                'markitup/sets/markdown/style.css',
            )]
        }

    def render(self, name, value, attrs=None):
        rendered = super(markItUpMarkdown, self).render(name, value, attrs)
        context = {
            'name': name,
        }
        return rendered + mark_safe(render_to_string(
            'admin/pages/page/widgets/markitupmarkdown.html', context))

class markItUpHTML(Textarea):
    class Media:
        js = [join(settings.PAGES_MEDIA_URL, path) for path in (
            'javascript/jquery.js',
            'markitup/jquery.markitup.js',
            'markitup/sets/default/set.js',
        )]
        css = {
            'all': [join(settings.PAGES_MEDIA_URL, path) for path in (
                'markitup/skins/simple/style.css',
                'markitup/sets/default/style.css',
            )]
        }

    def render(self, name, value, attrs=None):
        rendered = super(markItUpHTML, self).render(name, value, attrs)
        context = {
            'name': name,
        }
        return rendered + mark_safe(render_to_string(
            'admin/pages/page/widgets/markituphtml.html', context))