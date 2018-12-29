# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin
from . import models
# Register your models here.
admin.site.register(models.Bug)
admin.site.register(models.Product)
admin.site.register(models.Component)
admin.site.register(models.Severity)
admin.site.register(models.Status)
