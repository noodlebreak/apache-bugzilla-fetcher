from __future__ import absolute_import

import os
import sys

from celery import Celery

PROJECT_ROOT = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
sys.path.insert(0, os.path.join(PROJECT_ROOT, 'apps'))

# set the default Django settings module for the 'celery' program.
os.environ['DJANGO_SETTINGS_MODULE'] = 'bugzilla.settings'

from django.conf import settings

app = Celery('bugzilla')

# Using a string here means the worker will not have to
# pickle the object when using Windows.
app.config_from_object('django.conf:settings')
app.config_from_object('celeryconfig')
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)
