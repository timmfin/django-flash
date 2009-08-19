# -*- coding: utf-8 -*-

"""Integration test cases.
"""

from django.conf import settings
from django.core.exceptions import SuspiciousOperation
from django.core.urlresolvers import reverse
from django.test import TestCase

from djangoflash.context_processors import CONTEXT_VAR
from djangoflash.middleware import FlashScope

from testproj.app import views


class IntegrationTestCase(TestCase):
    """Test the middleware and the context processors working within a real
    Django application.
    """
    def _flash(self):
        """Shortcut to get the flash from the view context.
        """
        return self.response.context[CONTEXT_VAR]

    def test_default_lifecycle(self):
        """Integration: a value should be automatically removed from the flash.
        """
        self.response = self.client.get(reverse(views.set_flash_var))
        self.assertEqual('Message', self._flash()['message'])

        self.response = self.client.get(reverse(views.render_template))
        self.assertEqual('Message', self._flash()['message'])

        # Flash value will be removed when this request hits the app
        self.response = self.client.get(reverse(views.render_template))
        self.assertFalse('message' in self._flash())

    def test_keep_lifecycle(self):
        """Integration: a value shouldn't be removed from the flash when it is kept.
        """
        self.response = self.client.get(reverse(views.set_flash_var))
        self.assertEqual('Message', self._flash()['message'])

        self.response = self.client.get(reverse(views.keep_var))
        self.assertEqual('Message', self._flash()['message'])

        # Flash value won't be removed now because it was explicitely kept
        self.response = self.client.get(reverse(views.render_template))
        self.assertEqual('Message', self._flash()['message'])

        # Flash value will be removed when this request hits the app
        self.response = self.client.get(reverse(views.render_template))
        self.assertFalse('message' in self._flash())

    def test_keep_decorator(self):
        """Integration: keep_messages decorator should behave exactly like keep.
        """
        self.response = self.client.get(reverse(views.set_flash_var))
        self.assertEqual('Message', self._flash()['message'])

        self.response = self.client.get(reverse(views.keep_var_decorator))
        self.assertEqual('Message', self._flash()['message'])

        # Flash value won't be removed now because it was explicitely kept
        self.response = self.client.get(reverse(views.render_template))
        self.assertEqual('Message', self._flash()['message'])

        # Flash value will be removed when this request hits the app
        self.response = self.client.get(reverse(views.render_template))
        self.assertFalse('message' in self._flash())

    def test_now_lifecycle(self):
        """Integration: an immediate value shouldn't survive the next request.
        """
        self.response = self.client.get(reverse(views.set_now_var))
        self.assertEqual('Message', self._flash()['message'])

        # Flash value will be removed when this request hits the app
        self.response = self.client.get(reverse(views.render_template))
        self.assertFalse('message' in self._flash())

    def test_discard_lifecycle(self):
        """Integration: a discarded value shouldn't survive to the next request.
        """
        self.response = self.client.get(reverse(views.discard_var))
        self.assertEqual('Message', self._flash()['message'])

        # Flash value will be removed when this request hits the app
        self.response = self.client.get(reverse(views.render_template))
        self.assertFalse('message' in self._flash())

    def test_multiple_variables_lifecycle(self):
        """Integration: the flash should control several values independently.
        """
        self.response = self.client.get(reverse(views.set_flash_var))
        self.assertEqual('Message', self._flash()['message'])

        self.response = self.client.get(reverse(views.set_another_flash_var))
        self.assertEqual('Message', self._flash()['message'])
        self.assertEqual('Another message', self._flash()['anotherMessage'])

        # 'message' will be removed when this request hits the app
        self.response = self.client.get(reverse(views.render_template))
        self.assertFalse('message' in self._flash())
        self.assertEqual('Another message', self._flash()['anotherMessage'])

        # 'anotherMessage' will be removed when this request hits the app
        self.response = self.client.get(reverse(views.render_template))
        self.assertFalse('message' in self._flash())
        self.assertFalse('anotherMessage' in self._flash())

    def test_remove_flash(self):
        """Integration: an empty flash should be provided when none is available.
        """
        self.response = self.client.get(reverse(views.remove_flash))
        self.assertTrue(isinstance(self._flash(), FlashScope))

    def test_replace_flash_with_invalid_object(self):
        """Integration: an exception should be raised when exposing an invalid object as being the flash.
        """
        self.assertRaises(SuspiciousOperation, self.client.get, reverse(views.replace_flash))

    def test_request_to_serve_view_without_ignore(self):
        """Integration: request to static resources should trigger the flash update.
        """
        self.response = self.client.get(reverse(views.set_flash_var))
        self.assertEqual('Message', self._flash()['message'])

        # Requests to static resources should trigger the flash update
        settings.FLASH_IGNORE_MEDIA = False
        settings.FLASH_IGNORE_STATIC_SERVE = False
        
        self.response = self.client.get(settings.MEDIA_URL + 'test.css')
        self.assertEqual(200, self.response.status_code)

        # Flash value will be removed when this request hits the app
        self.response = self.client.get(reverse(views.render_template))
        self.assertFalse('message' in self._flash())

    def test_request_to_serve_view_with_media_url_ignore(self):
        """Integration: request to static resources should not trigger the flash update using FLASH_IGNORE_MEDIA.
        """
        self.response = self.client.get(reverse(views.set_flash_var))
        self.assertEqual('Message', self._flash()['message'])

        # Requests to static resources should not trigger the flash update
        settings.FLASH_IGNORE_MEDIA = True
        settings.FLASH_IGNORE_STATIC_SERVE = False

        self.response = self.client.get(settings.MEDIA_URL + 'test.css')
        self.assertEqual(200, self.response.status_code)

        self.response = self.client.get(reverse(views.render_template))
        self.assertEqual('Message', self._flash()['message'])

        # Flash value will be removed when this request hits the app
        self.response = self.client.get(reverse(views.render_template))
        self.assertFalse('message' in self._flash())

    def test_request_to_serve_view_with_resolve_static_ignore(self):
        """Integration: request to static resources should not trigger the flash update using FLASH_IGNORE_STATIC_SERVE.
        """
        self.response = self.client.get(reverse(views.set_flash_var))
        self.assertEqual('Message', self._flash()['message'])

        # Requests to static resources should not trigger the flash update
        settings.FLASH_IGNORE_MEDIA = False
        settings.FLASH_IGNORE_STATIC_SERVE = True

        self.response = self.client.get(settings.MEDIA_URL + 'test.css')
        self.assertEqual(200, self.response.status_code)

        self.response = self.client.get(reverse(views.render_template))
        self.assertEqual('Message', self._flash()['message'])

        # Flash value will be removed when this request hits the app
        self.response = self.client.get(reverse(views.render_template))
        self.assertFalse('message' in self._flash())
