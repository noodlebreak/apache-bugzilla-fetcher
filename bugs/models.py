# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models
from django.contrib.postgres.fields import ArrayField

# Create your models here.


class Classification(models.Model):
    name = models.CharField(max_length=200, unique=True)


class Component(models.Model):
    product = models.CharField(max_length=200)
    name = models.CharField(max_length=200)

    class Meta:
        unique_together = (('product', 'name'), )


class Flag(models.Model):
    name = models.CharField(max_length=200, unique=True)


class Group(models.Model):
    name = models.CharField(max_length=200, unique=True)


class Keyword(models.Model):
    name = models.CharField(max_length=200, unique=True)


class OpSys(models.Model):
    name = models.CharField(max_length=200, unique=True)


class Platform(models.Model):
    name = models.CharField(max_length=200, unique=True)


class Priority(models.Model):
    name = models.CharField(max_length=200, unique=True)


class Product(models.Model):
    name = models.CharField(max_length=200, unique=True)


class Severity(models.Model):
    name = models.CharField(max_length=200, unique=True)


class Status(models.Model):
    name = models.CharField(max_length=200, unique=True)


class TargetMilestone(models.Model):
    name = models.CharField(max_length=200, unique=True)


class Bug(models.Model):
    bz_id = models.IntegerField(db_index=True)
    alias = models.CharField(max_length=50)
    assigned_to = models.ForeignKey('auth.User', null=True, blank=True, related_name='assigned_bugs')

    blocks = ArrayField(models.IntegerField(), blank=True)

    cc = models.ForeignKey('auth.User', null=True, blank=True, related_name='ccd_bugs')
    classification = models.ForeignKey(Classification, null=True, blank=True)
    component = models.ForeignKey(Component)

    creation_time = models.DateTimeField()
    creator = models.ForeignKey('auth.User', related_name='created_bugs')

    deadline = models.DateTimeField(null=True, blank=True)
    depends_on = ArrayField(models.IntegerField(), blank=True)
    dupe_of = models.IntegerField(null=True, blank=True)
    flags = models.ManyToManyField(Flag, blank=True)
    groups = models.ManyToManyField(Group, blank=True)

    is_cc_accessible = models.BooleanField(default=False)
    is_confirmed = models.BooleanField(default=False)
    is_creator_accessible = models.BooleanField(default=False)
    is_open = models.BooleanField(default=False)
    keywords = models.ManyToManyField(Keyword, blank=True)
    last_change_time = models.DateTimeField(null=True, blank=True)
    op_sys = models.ForeignKey(OpSys, null=True, blank=True)
    platform = models.ForeignKey(Platform, null=True, blank=True)
    priority = models.ForeignKey(Priority, null=True, blank=True)
    product = models.ForeignKey(Product)

    qa_contact = models.ForeignKey('auth.User', null=True, blank=True, related_name='qa_bugs')
    resolution = models.TextField(blank=True)
    see_also = ArrayField(models.IntegerField(), blank=True)
    severity = models.ForeignKey(Severity)
    status = models.ForeignKey(Status)
    summary = models.TextField(blank=True)
    target_milestone = models.ForeignKey(TargetMilestone, null=True, blank=True)
    url = models.URLField(max_length=512, null=True, blank=True)
    version = models.CharField(max_length=10, null=True, blank=True)
    whiteboard = models.TextField(blank=True)

    def __str__(self):
        return self.bz_id
