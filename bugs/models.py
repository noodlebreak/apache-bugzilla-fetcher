from __future__ import unicode_literals

from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.contrib.auth.models import PermissionsMixin
from django.contrib.postgres.fields import ArrayField
from django.conf import settings
from django.core.mail import send_mail
from django.db import models
from django.utils.translation import ugettext_lazy as _


class UserManager(BaseUserManager):
    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        """
        Creates and saves a User with the given email and password.
        """
        if not email:
            raise ValueError('The given email must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password, **extra_fields):
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self._create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(_('email address'), max_length=255, unique=True)
    name = models.CharField(_('first name'), max_length=150, blank=True)

    is_active = models.BooleanField(_('active'), default=True)
    is_superuser = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    class Meta:
        verbose_name = _('user')
        verbose_name_plural = _('users')

    def get_full_name(self):
        '''
        Returns the first_name plus the last_name, with a space in between.
        '''
        full_name = '%s %s' % (self.first_name, self.last_name)
        return full_name.strip()

    def get_short_name(self):
        '''
        Returns the short name for the user.
        '''
        return self.first_name

    def email_user(self, subject, message, from_email=None, **kwargs):
        '''
        Sends an email to this User.
        '''
        send_mail(subject, message, from_email, [self.email], **kwargs)


class SingleFieldModelBase(models.Model):
    name = models.CharField(max_length=200, unique=True)

    class Meta:
        abstract = True

    def __str__(self):
        return self.name


class Classification(SingleFieldModelBase):
    pass


class Component(SingleFieldModelBase):
    product = models.CharField(max_length=200)

    class Meta:
        unique_together = (('product', 'name'), )


class Flag(SingleFieldModelBase):
    pass


class Group(SingleFieldModelBase):
    pass


class Keyword(SingleFieldModelBase):
    pass


class OpSys(SingleFieldModelBase):
    pass


class Platform(SingleFieldModelBase):
    pass


class Priority(SingleFieldModelBase):
    pass


class Product(SingleFieldModelBase):
    pass


class Severity(SingleFieldModelBase):
    pass


class Status(SingleFieldModelBase):
    pass


class TargetMilestone(SingleFieldModelBase):
    pass


class Bug(models.Model):
    bz_id = models.IntegerField(db_index=True)
    alias = models.CharField(max_length=50)
    assigned_to = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, related_name='assigned_bugs')

    blocks = ArrayField(models.IntegerField(), null=True, blank=True)

    cc = models.ManyToManyField(settings.AUTH_USER_MODEL, blank=True, related_name='ccd_bugs')
    classification = models.ForeignKey(Classification, null=True, blank=True)
    component = models.ForeignKey(Component)

    creation_time = models.DateTimeField()
    creator = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='created_bugs')

    deadline = models.DateTimeField(null=True, blank=True)
    depends_on = ArrayField(models.IntegerField(), null=True, blank=True)
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

    qa_contact = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, related_name='qa_bugs')
    resolution = models.TextField(blank=True)
    see_also = ArrayField(models.IntegerField(), null=True, blank=True)
    severity = models.ForeignKey(Severity)
    status = models.ForeignKey(Status)
    summary = models.TextField(blank=True)
    target_milestone = models.ForeignKey(TargetMilestone, null=True, blank=True)
    url = models.URLField(max_length=512, null=True, blank=True)
    version = models.CharField(max_length=100, null=True, blank=True)
    whiteboard = models.TextField(blank=True)

    def __str__(self):
        return str(self.bz_id)
