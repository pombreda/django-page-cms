# -*- coding: utf-8 -*-
import re
from django.core.urlresolvers import get_mod_func
from django.utils.translation import ugettext_lazy as _
from django.core.urlresolvers import reverse
from django.core.cache import cache
from pages import settings
from pages.models import Page, Content
from pages.utils import get_placeholders
from pages.lib.BeautifulSoup import BeautifulSoup


def get_connected_models():

    if not settings.PAGE_CONNECTED_MODELS:
        return []

    models = []
    for capp in settings.PAGE_CONNECTED_MODELS:
        model = {}
        mod_name, form_name = get_mod_func(capp['form'])
        f = getattr(__import__(mod_name, {}, {}, ['']), form_name)
        model['form'] = f
        mod_name, model_name = get_mod_func(capp['model'])
        model['model_name'] = model_name
        m = getattr(__import__(mod_name, {}, {}, ['']), model_name)
        model['model'] = m
        model['fields'] = []
        for k, v in f.base_fields.iteritems():
            if k is not "page":
                model['fields'].append((model_name.lower() + '_' + k, k, v))
        models.append(model)

    return models

# (extra) pagelink
def get_pagelink_absolute_url(page, language=None):
    """
    get the url of this page, adding parent's slug - with not cache usage
    """
    url = u'%s/' % page.slug(language)
    for ancestor in page.get_ancestors(ascending=True):
        url = ancestor.slug(language) + u'/' + url

    return reverse('pages-root') + url

# (extra) pagelink    
def valide_url(value):
    """
    return 1 if URL is validate
    """
    if value == u'':
        return 1
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
        return 0
    return 1

# (extra) pagelink
def get_body_pagelink_ids(page):
    """
    return all 'page_ID' found in body content.
    """
    pagelink_ids = []
    for placeholder in get_placeholders(page.get_template()):
        if placeholder.widget in settings.PAGE_LINK_EDITOR:
            for language in page.get_languages():
                try:
                    content = Content.objects.filter(language=language, type=placeholder.name, page=page).latest()
                    body = BeautifulSoup(content.body)
                    # find page link ID
                    tags = body.findAll('a', {'class': re.compile('^page_[0-9]*$')})
                    if len(tags) > 0:
                        for tag in tags:
                            tag_class = tag.get('class','')
                            if tag_class !='':
                                pagelink_ids.append(tag_class.replace('page_',''))
                except:
                    pass

    if pagelink_ids:
        return list(set(pagelink_ids)) # remove duplicates        
    else:
        return None


PAGE_CONTENT_DICT_KEY = "page_content_dict_%s_%s"

# (extra) pagelink
def set_body_pagelink(page, initial_pagelink_ids=None):
    """
    Set or update page link(s) with slug and title based on the class 'page_ID'
    + set or update 'externallink_broken' db value if invalide URL found and add class 
      or remove 'externallink_broken' (url minimum need '://' string to be tested) 
    + set or update number of 'pagelink_broken'
    """
    pagelink_ids = []
    externallink_broken = pagelink_broken = 0
    for placeholder in get_placeholders(page.get_template()):
        if placeholder.widget in settings.PAGE_LINK_EDITOR:
            content_dict = {}            
            for language in page.get_languages():
                try:
                    content = Content.objects.filter(language=language, type=placeholder.name, page=page).latest()
                    body = BeautifulSoup(content.body)

                    # find page link ID
                    tags = body.findAll('a', {'class': re.compile('^page_[0-9]*$')})
                    if tags:
                        for tag in tags:
                            tag_class = tag.get('class','')
                            if tag_class:
                                pagelink_ids.append(tag_class.replace('page_',''))

                    # find broken page link
                    tags = body.findAll('a', {'class': 'pagelink_broken'})
                    for tag in tags:
                        if tag.string:
                            pagelink_broken += 1
                        else:
                            # remove empty tags (prevent false-positive broken page link)
                            tag.replaceWith('');

                    # find external link
                    tags = body.findAll('a')
                    if tags:
                        for tag in tags:
                            if tag['href']:
                                tag_title = tag.get('title', '')
                                if tag.string:
                                    # check URL validity, set class 'externallink_broken' if link return a 404
                                    if '://' in tag['href'] and not valide_url(tag['href']):
                                        externallink_broken += 1
                                        tag.replaceWith('<a class="externallink_broken" title="'+tag_title \
                                                                 +'" href="'+tag['href']+'">'+tag.string+'</a>')
                                else:
                                    # remove empty tag (prevent false-positive)
                                    tag.replaceWith('')

                        content.body = unicode(body)
                        content.save()
                    content_dict[language] = content.body
                except Content.DoesNotExist:
                    content_dict[language] = ''
            cache.set(PAGE_CONTENT_DICT_KEY % (str(page.id), placeholder.name), content_dict)

    page.externallink_broken = externallink_broken
    page.pagelink_broken = pagelink_broken
    page.save()
 
    pagelink_ids = list(set(pagelink_ids)) # remove duplicates 

    # update 'pagelink', if link removed from body
    init_pagelink_ids = []
    if initial_pagelink_ids is not None: 
        removed_pagelink_ids =  [id for id in initial_pagelink_ids if id not in pagelink_ids]
        for pk, obj in Page.objects.in_bulk(removed_pagelink_ids).items():
            if obj.pagelink:
                init_pagelink_ids = obj.pagelink.split(',')
                if init_pagelink_ids:
                    if str(page.id) not in init_pagelink_ids:
                        init_pagelink_ids.append(str(page.id))
                else:
                    init_pagelink_ids = str(page.id)
            else:
                init_pagelink_ids = str(page.id)

            if init_pagelink_ids:
                obj.pagelink = ','.join(init_pagelink_ids)
                obj.save()

    # set/update 'pagelink' list
    for pk, obj in Page.objects.in_bulk(pagelink_ids).items():
        if obj.pagelink is not None:            
            pagelink_ids = obj.pagelink.split(',')
            if str(page.id) not in pagelink_ids:
                pagelink_ids.append(str(page.id))
        else:
            pagelink_ids = str(page.id)

        if pagelink_ids:
            obj.pagelink = ','.join(pagelink_ids)
            obj.save()

        # set/update all page link 'a' tags of body content
        for placeholder in get_placeholders(page.get_template()):
            if placeholder.widget in settings.PAGE_LINK_EDITOR:
                content_dict = {}                
                for language in page.get_languages():
                    try:
                        content = Content.objects.filter(language=language, type=placeholder.name, page=page).latest()
                        body = BeautifulSoup(content.body)
                        tags = body.findAll('a', attrs={'class': 'page_'+str(obj.id)})
                        if tags:
                            for tag in tags:
                                if tag.string:
                                    tag.replaceWith('<a class="page_'+str(obj.id)+'" title="'+obj.title(language) \
                                                        +'" href="'+get_pagelink_absolute_url(obj, language)+'">'+tag.string+'</a>')
                                else:
                                    # remove empty tag (prevent false-positive)
                                    tag.replaceWith('')
                            content.body = unicode(body)
                            content.save()
                        content_dict[language] = content.body
                    except Content.DoesNotExist:
                        content_dict[language] = ''
                cache.set(PAGE_CONTENT_DICT_KEY % (str(page.id), placeholder.name), content_dict)

# (extra) pagelink
def update_body_pagelink(page):
    """
    update internal link(s) of body content, specialy the 'url' and 
    of all there children.
    """
    if page.pagelink is not None:
        pagelink_ids = page.pagelink.split(',')
        if pagelink_ids:
            for pk, obj in Page.objects.in_bulk(pagelink_ids).items():
                for placeholder in get_placeholders(obj.get_template()):
                    if placeholder.widget in settings.PAGE_LINK_EDITOR:
                        content_dict = {}                        
                        for language in obj.get_languages():
                            try:
                                content = Content.objects.filter(language=language, type=placeholder.name, page=obj).latest()
                                body = BeautifulSoup(content.body)                    
                                tags = body.findAll('a', attrs={'class': 'page_'+str(page.id)})
                                if tags:                        
                                    for tag in tags:
                                        if tag.string:
                                            tag.replaceWith('<a class="page_'+str(page.id)+'" title="'+page.title(language) \
                                                        +'" href="'+get_pagelink_absolute_url(page, language)+'">'+tag.string+'</a>')
                                else:
                                    # remove empty tag (prevent false-positive)
                                    tag.replaceWith('')
                                content.body = unicode(body)
                                content.save()
                                content_dict[language] = content.body
                            except Content.DoesNotExist:
                                content_dict[language] = ''              
                        cache.set(PAGE_CONTENT_DICT_KEY % (str(obj.id), placeholder.name), content_dict)

    # update new 'url' of children pages 
    for children_page in page.children.all():
        if children_page.pagelink is not None:
            pagelink_ids = children_page.pagelink.split(',')
            if pagelink_ids:
                for pk,obj in Page.objects.in_bulk(pagelink_ids).items():
                    for placeholder in get_placeholders(obj.get_template()):
                        if placeholder.widget in settings.PAGE_LINK_EDITOR:
                            content_dict = {}
                            for language in obj.get_languages():
                                try:
                                    content = Content.objects.filter(language=language, type=placeholder.name, page=obj).latest()
                                    body = BeautifulSoup(content.body)
                                    tags = body.findAll('a', attrs={'class': 'page_'+str(page.id)})
                                    if tags:
                                        for tag in tags:
                                            if tag.string:
                                                tag.replaceWith('<a class="page_'+str(page.id)+'" title="'+page.title(language) \
                                                            +'" href="'+get_pagelink_absolute_url(page, language)+'">'+tag.string+'</a>')
                                            else:
                                                # remove empty tag (prevent false-positive)
                                                tag.replaceWith('')
                                        content.body = unicode(body)                          
                                        content.save() 
                                    content_dict[language] = content.body
                                except Content.DoesNotExist:
                                    content_dict[language] = ''                    
                            cache.set(PAGE_CONTENT_DICT_KEY % (str(obj.id), placeholder.name), content_dict)

# (extra) pagelink
def delete_body_pagelink_by_language(page, language):
    """
    set class 'pagelink_broken' of all 'a' tags of body for a language.
    + clear pagelink page ID entries.
    """
    if page.pagelink is not None:
        pagelink_ids = page.pagelink.split(',')
        if pagelink_ids:
            for pk, obj in Page.objects.in_bulk(pagelink_ids).items():
                if obj.id != page.id:
                    pagelink_broken = 0
                    for placeholder in get_placeholders(obj.get_template()):
                        if placeholder.widget in settings.PAGE_LINK_EDITOR:
                            try:
                                content = Content.objects.filter(language=language, type=placeholder.name, page=obj).latest()
                                body = BeautifulSoup(content.body)
                                tags = body.findAll('a', attrs={'class': 'page_'+str(page.id)})
                                if tags:
                                    for tag in tags:
                                        if tag.string:
                                            pagelink_broken += 1                                        
                                            tag.replaceWith('<a class="pagelink_broken" title="'+page.title(language) \
                                                                +'" href="'+get_pagelink_absolute_url(page, language)+'">'+tag.string+'</a>')
                                        else:
                                            # remove empty tag (prevent false-positive)
                                            tag.replaceWith('')
                                    content.body = unicode(body)
                                    content.save()
                                    cache.delete(PAGE_CONTENT_DICT_KEY % (str(obj.id), placeholder.name))
                            except Content.DoesNotExist:
                                pass                    
                    obj.pagelink_broken = pagelink_broken
                    obj.save()

    # find page link ID
    pagelink_ids = language_pagelink_ids = []
    externallink_broken = 0
    for placeholder in get_placeholders(page.get_template()):
        if placeholder.widget in settings.PAGE_LINK_EDITOR:
            pagelink_broken = 0
            for lang in page.get_languages():
                try:
                    content = Content.objects.filter(language=lang, type=placeholder.name, page=page).latest()
                    body = BeautifulSoup(content.body)
                    tags = body.findAll('a', {'class': re.compile('^page_[0-9]*$')})
                    if tags:
                        for tag in tags:
                            tag_class = tag.get('class','')
                            if tag_class:
                                pagelink_ids.append(tag_class.replace('page_',''))
                                if lang != language:
                                    language_pagelink_ids.append(tag_class.replace('page_',''))

                    if lang != language:
                        # find broken external link
                        tags = body.findAll('a', {'class': 'externallink_broken'})
                        for tag in tags:
                            if tag.string:
                                externallink_broken += 1
                            else:
                                # remove empty tags (prevent false-positive broken page link)
                                tag.replaceWith('');
                except Content.DoesNotExist:
                    pass

    page.externallink_broken = externallink_broken
    page.save()

    
    pagelink_ids = list(set(pagelink_ids)) # remove duplicates
    language_pagelink_ids = list(set(language_pagelink_ids)) # remove duplicates
   
    # update 'pagelink's, remove page.id
    for pk, obj in Page.objects.in_bulk(pagelink_ids).items():
        if obj.pagelink is not None:
            obj_pagelink_ids = obj.pagelink.split(',')
            if obj_pagelink_ids:
                if str(page.id) in obj_pagelink_ids and str(obj.id) not in language_pagelink_ids: 
                    obj_pagelink_ids.remove(str(page.id))
                    if not obj_pagelink_ids:
                        obj.pagelink = ''
                    else:
                        obj.pagelink = obj_pagelink_ids
                    obj.save()
