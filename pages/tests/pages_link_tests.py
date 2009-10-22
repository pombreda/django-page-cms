# -*- coding: utf-8 -*-
"""Django page CMS test suite module for page links"""
import django
from django.test.client import Client

from pages import settings
from pages.tests.testcase import TestCase
from pages.models import Page, Content, PageAlias
from pages.pagelinks import validate_url, get_pagelink_ids, set_pagelink, \
         make_pagelink, update_pagelink, delete_pagelink_by_language, update_broken_links

class LinkTestCase(TestCase):
    """Django page CMS ``pagelink`` test suite class"""

    def test_01_valide_url(self):
        """Test the ``valide_url`` function."""
        self.assertTrue(validate_url(""))
        self.assertTrue(validate_url("http://www.google.com"))
        self.assertFalse(validate_url("http://tot"))

    def test_02_get_pagelink_ids(self):
        """Test the ``get_pagelink_ids`` functions."""
        page1 = self.create_new_page()
        page2 = self.create_new_page()
        content_string = 'test <a href="%s" class="page_%d">hello</a>'
        content = Content(
            page=page2,
            language='en-us',
            type='body',
            body=content_string % (page1.get_absolute_url(language='en-us'), page1.id)
        )
        content.save()
        self.assertEqual(get_pagelink_ids(page2), [unicode(page1.id)])

    def test_03_set_pagelink(self):
        """Test the ``set_pagelink`` functions."""
        page1 = self.create_new_page()
        page2 = self.create_new_page()
        content_string = 'test <a href="%s" class="page_%d">hello</a>'
        content = Content(
            page=page2,
            language='en-us',
            type='body',
            body=content_string % (page1.get_absolute_url(language='en-us'), page1.id)
        )
        content.save()
        self.assertEqual(get_pagelink_ids(page2), [unicode(page1.id)])

        set_pagelink(page2, page1)
        content = Content.objects.filter(
            page=page2, language='en-us', type='body').latest()

        content_string = 'test <a href="%s" class="page_%d" title="%s">hello</a>' \
            % (page1.get_absolute_url(language='en-us'), page1.id, page1.title(language='en-us'))
        self.assertEqual(content.body, content_string)

    def test_04_make_pagelink(self):
        """Test the ``make_pagelink`` functions."""
        page1 = self.create_new_page()
        page2 = self.create_new_page()
        content_string = 'test <a href="%s" class="page_%d">hello</a>'
        content = Content(
            page=page2,
            language='en-us',
            type='body',
            body=content_string % (page1.get_absolute_url(language='en-us'), page1.id)
        )
        content.save()        

        make_pagelink(page2, get_pagelink_ids(page2))
        content = Content.objects.filter(
            page=page2, language='en-us', type='body').latest()

        content_string = 'test <a href="%s" class="page_%d" title="%s">hello</a>' \
            % (page1.get_absolute_url(language='en-us'), page1.id, page1.title(language='en-us'))
        self.assertEqual(content.body, content_string)

    def text_05_update_pagelink(self):
        """Test the ``update_pagelink`` functions."""
        page1 = self.create_new_page()
        page2 = self.create_new_page()
        content_string = 'test <a href="%s" class="page_%d">hello</a>'
        content = Content(
            page=page2,
            language='en-us',
            type='body',
            body=content_string % (page1.get_absolute_url(language='en-us'), page1.id)
        )
        content.save()

        client = Client()
        client.login(username='batiste', password='b')
        response = client.post('/admin/pages/page/%d/move-page/' % page2.id,
            {'position':'first-child', 'target':page1.id})
        page2 = Page.objects.get(id=page2.id)
        self.assertTrue(page1.parent == page2)
        content = Content.objects.filter(
            page=page2, language='en-us', type='body').latest()
        content_string = 'test <a href="%s" class="page_%d" title="%s">hello</a>' \
            % (page1.get_absolute_url(language='en-us', in_cache=False), page1.id, page1.title(language='en-us'))
        self.assertEqual(content.body, content_string)
        

    def test_06_update_broken_links(self):
        """Test the ``update_broken_links`` function."""
        page1 = self.create_new_page()
        page2 = self.create_new_page()
        page3 = self.create_new_page()
        content_string = 'test <a href="%s" class="page_%d">hello</a>'
        content = Content(
            page=page2,
            language='en-us',
            type='body',
            body=content_string % (page1.get_absolute_url(language='en-us'), page1.id)
        )        
        content.save()
        
        content = Content(
            page=page3,
            language='en-us',
            type='body',
            body=content_string % (page1.get_absolute_url(language='en-us'), page1.id) + \
                    content_string % (page2.get_absolute_url(language='en-us'), page2.id)
        )
        content.save()
                
        make_pagelink(page3, get_pagelink_ids(page3))
        update_broken_links(page2, page3, Content)
        page3 = Page.objects.get(id=page3.id)    
        content = Content.objects.filter(
            page=page3, language='en-us', type='body').latest()
        content_string = 'test <a href="%s" class="page_%d" title="%s">hello</a>' \
            % (page1.get_absolute_url(language='en-us'), page1.id, page1.title(language='en-us')) + \
            'test <a href="/pages/test-page-2/" class="pagelink_broken" title="test page 2">hello</a>'
        self.assertEqual(content.body, content_string)

    def test_07_delete_pagelink_by_language(self):
        """Test the ``delete_pagelink_by_language`` function."""
        c = Client()
        user = c.login(username= 'batiste', password='b')

        # first page `english`
        page_data1 = self.get_new_page_data()
        page_data1["title"] = 'english title 1'
        page_data1["slug"] = 'english-title-1'
        response = c.post('/admin/pages/page/add/', page_data1)
        self.assertRedirects(response, '/admin/pages/page/')
        page1 = Page.objects.all()[0]

        # add a french version of the same page
        page_data1["language"] = 'fr-ch'
        page_data1["title"] = 'french title 1'
        page_data1["slug"] = 'french-title-1'
        response = c.post('/admin/pages/page/%d/' % page1.id, page_data1)        
        self.assertRedirects(response, '/admin/pages/page/')       

        # second page `english`
        page_data2 = self.get_new_page_data()
        page_data2["title"] = 'english title 2'
        page_data2["slug"] = 'english-title-2'
        response = c.post('/admin/pages/page/add/', page_data2)
        self.assertRedirects(response, '/admin/pages/page/')
        page2 = Page.objects.all()[1]

        # add a french version of the same page
        page_data2["language"] = 'fr-ch'
        page_data2["title"] = 'french title 2'
        page_data2["slug"] = 'french-title-2'
        response = c.post('/admin/pages/page/%d/' % page2.id, page_data2)
        self.assertRedirects(response, '/admin/pages/page/')        
        
        content_string = 'test <a href="%s" class="page_%d">hello</a>'
        content = Content(
            page=page2,
            language='en-us',
            type='body',
            body=content_string % (page1.get_absolute_url(language='en-us'), page1.id)
        )
        content.save()

        content = Content(
            page=page2,
            language='fr-ch',
            type='body',
            body=content_string % (page1.get_absolute_url(language='fr-ch'), page1.id)
        )
        content.save()

        make_pagelink(page2, get_pagelink_ids(page2))
        response = c.post('/admin/pages/page/%d/delete-content/fr-ch/' % page1.id)
        self.assertRedirects(response,'/admin/pages/page/%d/' % page1.id)

        page2 = Page.objects.get(id=page2.id)
        content = Content.objects.filter(
            page=page2, language='fr-ch', type='body').latest()
        content_string = 'test <a href="/pages/french-title-1/" class="pagelink_broken" title="french title 1">hello</a>'
        self.assertEqual(content.body, content_string)
        content = Content.objects.filter(
            page=page2, language='en-us', type='body').latest()
        content_string = 'test <a href="%s" class="page_%d" title="%s">hello</a>' \
            % (page1.get_absolute_url(language='en-us'), page1.id, page1.title(language='en-us'))
        self.assertEqual(content.body, content_string)

    def test_08_broken_links(self):
        """Test brokens links."""
        c = Client()
        user = c.login(username= 'batiste', password='b')

        page1 = self.create_new_page()
        page2 = self.create_new_page()
        page3 = self.create_new_page()
        content_string = 'test <a href="%s" class="page_%d">hello</a>'
        content_string_broken = 'test <a href="%s" class="pagelink_broken" title="%s">hello</a>'
        content = Content(
            page=page2,
            language='en-us',
            type='body',
            body=content_string % (page1.get_absolute_url(language='en-us'), page1.id)
        )
        content.save()

        content = Content(
            page=page3,
            language='en-us',
            type='body',
            body=content_string % (page1.get_absolute_url(language='en-us'), page1.id) + \
                    content_string_broken % (page2.get_absolute_url(language='en-us'), page2.title(language='en-us'))
        )
        content.save()

        make_pagelink(page3, get_pagelink_ids(page3))
        self.assertEqual(page3.pagelink_broken, 1)
        update_broken_links(page1, page2, Content)
        update_broken_links(page1, page3, Content)

        page3 = Page.objects.get(id=page3.id)
        self.assertEqual(page3.pagelink_broken, 2)
