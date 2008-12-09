from django import forms
from django.template.defaultfilters import slugify
from django.utils.translation import ugettext_lazy as _

from pages import settings
from pages.models import Page, Content, tagging
from pages.admin.utils import unique_slug_for_parent

class PageForm(forms.ModelForm):
    title = forms.CharField(
        label=_('Title'),
        widget=forms.TextInput(),
        help_text=_('The default title')
    )
    slug = forms.CharField(
        label=_('Slug'),
        widget=forms.TextInput(),
        help_text=_('The part of the title that is used in permalinks')
    )
    language = forms.ChoiceField(
        label=_('Language'),
        choices=settings.PAGE_LANGUAGES,
        help_text=_('The current language of the content fields.'),
    )
    template = forms.ChoiceField(
        required=False,
        label=_('Template'),
        choices=settings.PAGE_TEMPLATES,
        help_text=_('The template used to render the content.')
    )
    target = forms.IntegerField(required=False)
    position = forms.CharField(required=False)

    if tagging:
        from tagging.forms import TagField
        from pages.admin.widgets import AutoCompleteTagInput
        tags = TagField(widget=AutoCompleteTagInput(), required=False)

    class Meta:
        model = Page

    def clean_slug(self):
        slug = slugify(self.cleaned_data['slug'])
        if settings.PAGE_UNIQUE_SLUG_REQUIRED:
            if self.instance.id:
                if Content.objects.exclude(page=self.instance).filter(body=slug, type="slug").count():
                    raise forms.ValidationError(_('Another page with this slug already exists'))
            elif Content.objects.filter(body=slug, type="slug").count():
                raise forms.ValidationError(_('Another page with this slug already exists'))
        else:
            target = self.data.get('target', None)
            position = self.data.get('position', None)
            if self.instance.id:
                sibling_slugs = [sibling.slug() for sibling in self.instance.get_siblings()]
                if slug in sibling_slugs:
                    raise forms.ValidationError(_('A sibling page with this slug already exists'))
            elif target is not None and position is not None:
                if position in ('left', 'right'):
                    if not unique_slug_for_parent(slug=slug, page_id=target, relationship='sibling'):
                        raise forms.ValidationError(_('A sibling page with this slug already exists'))
                elif position == 'first-child':
                    if not unique_slug_for_parent(slug=slug, page_id=target, relationship='parent'):
                        raise forms.ValidationError(_('A sibling page with this slug already exists'))
        return slug
