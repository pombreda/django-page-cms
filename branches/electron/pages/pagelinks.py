# -*- coding: utf-8 -*-
"""A collection of functions for ``PageLink`` system"""
import re
from django.core.urlresolvers import reverse
from django.core.cache import cache
from pages.utils import get_placeholders
from pages import settings


PAGE_BROKEN_LINK_KEY = "page_broken_link_%s"
PAGE_CONTENT_DICT_KEY = "page_content_dict_%s_%s"
PAGE_CLASS_ID_REGEX = re.compile('page_[0-9]+')

def get_content_tree(page, language, placeholder_name, Content):
    """Get ``BeautifulSoup`` tree"""
    from BeautifulSoup import BeautifulSoup
    content = Content.objects.filter(
                    language=language,
                    type=placeholder_name,
                    page=page
                ).latest()
    return BeautifulSoup(content.body), content

def validate_url(value):
    """
    return ``True`` if URL is validate
    """
    if not value:
        return True
    import urllib2
    headers = {
        "Accept": "text/xml,application/xml,application/xhtml+xml,text/html;q=0.9,text/plain;q=0.8,image/png,*/*;q=0.5",
        "Accept-Language": "en-us,en;q=0.5",
        "Accept-Charset": "ISO-8859-1,utf-8;q=0.7,*;q=0.7",
        "Connection": "close",
        "User-Agent": settings.PAGE_URL_VALIDATOR_USER_AGENT,
    }
    try:
        req = urllib2.Request(value, None, headers)
        u = urllib2.urlopen(req)
    except:
        return False
    return True

def get_pagelink_ids(page):
    """
    return all 'page_ID' found in content.
    """
    from pages.models import Content
    pagelink_ids = []
    for placeholder in get_placeholders(page.get_template()):
        if placeholder.widget in settings.PAGE_LINK_EDITOR:
            for lang in page.get_languages():
                try:
                    tree, content = get_content_tree(page, lang, placeholder.name, Content)
                    # find page 'page_ID'
                    for tag in tree.findAll('a', {'class': PAGE_CLASS_ID_REGEX}):
                        pagelink_ids.append(tag['class'].replace('page_',''))
                except Content.DoesNotExist:
                    pass

    if pagelink_ids:
        return list(set(pagelink_ids)) # remove duplicates
    else:
        return None

def set_pagelink(page, target):
    """Set or update 'href' and 'title' of a page."""
    from pages.models import Content
    for placeholder in get_placeholders(page.get_template()):
            if placeholder.widget in settings.PAGE_LINK_EDITOR:
                content_dict = {}
                for lang in page.get_languages():
                    try:
                        tree, content = get_content_tree(page, lang, placeholder.name, Content)
                        for tag in tree.findAll('a', {'class': 'page_'+str(target.id)}):
                            if tag.string and tag.string.strip():
                                tag['title'] = target.title(lang)
                                tag['href'] = target.get_absolute_url(lang, in_cache=False)
                        content.body = unicode(tree)
                        content.save()
                        content_dict[lang] = content.body
                    except Content.DoesNotExist:
                        content_dict[lang] = ''
                cache.set(PAGE_CONTENT_DICT_KEY %
                    (str(page.id), placeholder.name), content_dict)

def make_pagelink(page, initial_pagelink_ids=None):
    """
    Set or update page link(s) with slug and title based on the class 'page_ID'
    + set or update 'externallink_broken' db value if invalide URL found 
    and add class or remove 'externallink_broken' 
    (url 'http://' string to be checked) 
    + set or update number of 'pagelink_broken'
    """
    from pages.models import Page, Content
    pagelink_ids = []
    externallink_broken = pagelink_broken = 0
    for placeholder in get_placeholders(page.get_template()):
        if placeholder.widget in settings.PAGE_LINK_EDITOR:
            content_dict = {}
            # analyze content by langugage
            for lang in page.get_languages():
                try:
                    tree, content = get_content_tree(page, lang, placeholder.name, Content)
                    for tag in tree.findAll('a'): # find all page link                                                    
                        if tag.string and tag.string.strip():
                            tag_class = tag.get('class', False)
                            if tag_class:
                                # find page link with class 'page_ID'
                                if PAGE_CLASS_ID_REGEX.match(tag_class) and \
                                        tag_class.replace('page_','') not in pagelink_ids:
                                    pagelink_ids.append(tag_class.replace('page_',''))
                                # find page link with class 'pagelink_broken'
                                if 'pagelink_broken' in tag_class:
                                    pagelink_broken += 1
                            # check URL validity
                            # set class 'externallink_broken' 
                            # if link return a 404
                            if 'http://' in tag.get('href','') \
                            and not validate_url(tag['href']):
                                externallink_broken += 1
                                tag['class'] = 'externallink_broken'
                        else:
                            # remove empty tag (prevent false-positive)
                            tag.extract()
                    content.body = unicode(tree)
                    content.save()
                    content_dict[lang] = content.body
                except Content.DoesNotExist:
                    content_dict[lang] = ''
            cache.set(PAGE_CONTENT_DICT_KEY %
                (str(page.id), placeholder.name), content_dict)
    page.externallink_broken = externallink_broken
    page.pagelink_broken = pagelink_broken
    page.save()

    pagelink_ids = list(set(pagelink_ids)) # remove duplicates

    # set/update 'pagelink' of pages concerned    
    for pk, target in Page.objects.in_bulk(pagelink_ids).items():
        if not target.pagelink:
            target.pagelink = str(page.id)
            target.save()
        else:
            target_pagelink_ids = target.pagelink.split(',')
            if target_pagelink_ids and target_pagelink_ids[0] !='' \
                    and str(page.id) not in target_pagelink_ids:
                target_pagelink_ids.append(str(page.id))
                target.pagelink = ','.join(list(set(target_pagelink_ids)))
                target.save()

        # set/update all link(s) for page target with link(s) of current page
        set_pagelink(page, target)

    # update 'pagelink', if link removed from body
    update_pagelink_ids = removed_pagelink_ids = []
    if initial_pagelink_ids is not None:
        removed_pagelink_ids_list =  [id for id in initial_pagelink_ids if id not in pagelink_ids]
        if removed_pagelink_ids_list and removed_pagelink_ids_list[0] !='':
            for pk, target in Page.objects.in_bulk(removed_pagelink_ids_list).items():
                if target.pagelink:
                    update_pagelink_ids_list = target.pagelink.split(',')
                    if update_pagelink_ids_list and update_pagelink_ids_list[0] !='' \
                            and str(page.id) in update_pagelink_ids_list:
                        update_pagelink_ids_list.remove(str(page.id))
                        if update_pagelink_ids_list and update_pagelink_ids_list[0] !='':
                            target.pagelink = ','.join(update_pagelink_ids_list)
                        else:
                            target.pagelink = ''
                        target.save()


# for pagelink (move on the tree)
def update_pagelink(page):
    """
    update page link(s) of content, specialy the 'href' and 'title'
    of all there children.
    """
    from pages.models import Page
    if page.pagelink is not None:
        pagelink_ids = page.pagelink.split(',')
        if pagelink_ids and pagelink_ids[0] !='':
            for pk, target in Page.objects.in_bulk(pagelink_ids).items():
                set_pagelink(target, page)

    # update new 'url' of children pages 
    for children_page in page.children.all():
        if children_page.pagelink is not None:
            pagelink_ids = children_page.pagelink.split(',')
            if pagelink_ids and pagelink_ids[0] !='':
                for pk, target in Page.objects.in_bulk(pagelink_ids).items():
                    set_pagelink(target, page)

def delete_pagelink_by_language(page, language):
    """
    set class 'pagelink_broken' of all 'a' tags of body for a language.
    + clear pagelink page ID entries.
    """
    from pages.models import Page, Content
    if page.pagelink is not None:
        pagelink_ids = page.pagelink.split(',')
        if pagelink_ids[0] !='':
            for pk, target in Page.objects.in_bulk(pagelink_ids).items():
                if target.id != page.id:
                    target_pagelink_broken = target_externallink_broken = 0
                    for placeholder in get_placeholders(target.get_template()):
                        if placeholder.widget in settings.PAGE_LINK_EDITOR:
                            for lang in target.get_languages():
                                try:
                                    tree, content = get_content_tree(target, lang, placeholder.name, Content)
                                    for tag in tree.findAll('a'):
                                        if tag.string and tag.string.strip():
                                            tag_class = tag.get('class', False)
                                            if tag_class:
                                                # for the removed language
                                                if lang == language:
                                                    # if link(s) with the page_id > set link to broken
                                                    if tag_class == 'page_' + str(page.id):
                                                        target_pagelink_broken += 1
                                                        tag['class'] = 'pagelink_broken'
                                                # for other language(s)
                                                else:
                                                    # count already broken page link(s)
                                                    if tag_class == 'pagelink_broken':
                                                        target_pagelink_broken += 1
                                                    # count already external broken link(s)
                                                    if tag_class == 'externallink_broken':
                                                        target_externallink_broken += 1
                                    content.body = unicode(tree)
                                    content.save()
                                except Content.DoesNotExist:
                                    pass
                            # clear cache entry
                            cache.delete(PAGE_CONTENT_DICT_KEY %
                                (str(target.id), placeholder.name))
                    target.pagelink_broken = target_pagelink_broken
                    target.externallink_broken = target_externallink_broken
                    target.save()

    # find 'page_ID' + count pagelink_broken and externallink_broken
    pagelink_ids = other_language_pagelink_ids = []
    pagelink_broken = externallink_broken = 0
    for placeholder in get_placeholders(page.get_template()):
        if placeholder.widget in settings.PAGE_LINK_EDITOR:
            for lang in page.get_languages():
                try:
                    tree, content = get_content_tree(page, lang, placeholder.name, Content)
                    for tag in tree.findAll('a'):
                        if tag.string and tag.string.strip():
                            tag_class = tag.get('class', False)
                            if tag_class:
                                if PAGE_CLASS_ID_REGEX.match(tag_class):
                                    pagelink_ids.append(tag_class.replace('page_',''))
                                    if lang != language:
                                        other_language_pagelink_ids \
                                            .append(tag_class.replace('page_',''))
                                # find broken external link
                                if lang != language:
                                    if tag_class == 'pagelink_broken':
                                        pagelink_broken += 1
                                    if tag_class == 'externallink_broken':
                                        externallink_broken += 1
                except Content.DoesNotExist:
                    pass
    page.pagelink_broken = pagelink_broken
    page.externallink_broken = externallink_broken
    page.save()

    # remove duplicates
    pagelink_ids = list(set(pagelink_ids))
    other_language_pagelink_ids = list(set(other_language_pagelink_ids))

    # update 'pagelink's, remove page.id
    for pk, target in Page.objects.in_bulk(pagelink_ids).items():
        if target.pagelink is not None:
            target_pagelink_ids = target.pagelink.split(',')
            if target_pagelink_ids[0] !='':
                if str(page.id) in target_pagelink_ids \
                        and str(target.id) not in other_language_pagelink_ids:
                    target_pagelink_ids.remove(str(page.id))
                    if target_pagelink_ids[0] !='':
                        target.pagelink = ','.join(target_pagelink_ids)
                    else:
                        target.pagelink = ''
                    target.save()


"""Used on ``Page`` model for ``delete`` method"""
def mark_deleted(content, page_id):
    from BeautifulSoup import BeautifulSoup
    tree = BeautifulSoup(content)
    broken_links = 0
    for tag in tree.findAll('a'):
        if tag.string and tag.string.strip():
            tag_class = tag.get('class', False)
            if tag_class:
                # mark link is broken
                if tag_class == 'page_'+str(page_id):             
                    tag['class'] = 'pagelink_broken'
                    broken_links += 1                    
                # count new and already broken page link(s)
                elif tag_class == 'pagelink_broken':
                    broken_links += 1    
    return unicode(tree), broken_links

def update_broken_links(page, target, Content):
    all_broken_links = 0    
    for placeholder in get_placeholders(target.get_template()):
        # this condition doesn't make that much sense to me
        # I removed it for now
        if placeholder.widget in settings.PAGE_LINK_EDITOR:
            for lang in target.get_languages():
                try:
                    tree, content = get_content_tree(target, lang, placeholder.name, Content)
                    content.body, broken_links \
                            = mark_deleted(content.body, page.id)
                    content.save()
                    all_broken_links += broken_links
                except Content.DoesNotExist:
                    pass
            cache.delete(PAGE_CONTENT_DICT_KEY %
                    (target.id, placeholder.name))
    target.pagelink_broken = all_broken_links
    target.save()
