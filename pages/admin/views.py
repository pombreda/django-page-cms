# -*- coding: utf-8 -*-
from django.shortcuts import get_object_or_404
from django.http import HttpResponse, Http404
from django.contrib.admin.views.decorators import staff_member_required

from pages import settings
from pages.models import Page, Content

from pages.utils import get_placeholders, auto_render

def change_status(request, page_id, status):
    """
    Switch the status of a page
    """
    if request.method == 'POST':
        page = Page.objects.get(pk=page_id)
        page.status = status
        page.save()
        return HttpResponse(unicode(page.status))
    raise Http404
change_status = staff_member_required(change_status)

def modify_content(request, page_id, content_id, language_id):
    if request.method == 'POST':
        content = request.POST.get('content', False)
        if not content:
            raise Http404
        page = Page.objects.get(pk=page_id)
        if settings.PAGE_CONTENT_REVISION:
            Content.objects.create_content_if_changed(page, language_id,
                                                      content_id, content)
        else:
            Content.objects.set_or_create_content(page, language_id,
                                                  content_id, content)
        page.invalidate()
        return HttpResponse('ok')
    raise Http404
modify_content = staff_member_required(modify_content)

def traduction(request, page_id, language_id):
    page = Page.objects.get(pk=page_id)
    context = {}
    lang = language_id
    placeholders = get_placeholders(page.get_template())
    if Content.objects.get_content(page, language_id, "title") is None:
        language_error = True
    return 'pages/traduction_helper.html', locals()
traduction = staff_member_required(traduction)
traduction = auto_render(traduction)

def get_content(request, page_id, content_id):
    content_instance = get_object_or_404(Content, pk=content_id)
    return HttpResponse(content_instance.body)
get_content = staff_member_required(get_content)
get_content = auto_render(get_content)

def valid_targets_list(request, page_id):
    """A list of valid targets to move a page"""
    if not settings.PAGE_PERMISSION:
        perms = "All"
    else:
        from pages.models import PagePermission
        perms = PagePermission.objects.get_page_id_list(request.user)
    query = Page.objects.valid_targets(page_id, request, perms)
    return HttpResponse(",".join([str(p.id) for p in query]))
valid_targets_list = staff_member_required(valid_targets_list)

def sub_menu(request, page_id):
    """Render the children of the requested page"""
    page = Page.objects.get(id=page_id)
    pages = page.children.all()
    has_permission = page.has_page_permission(request)
    return "admin/pages/page/sub_menu.html", locals()
    
sub_menu = staff_member_required(sub_menu)
sub_menu = auto_render(sub_menu)
