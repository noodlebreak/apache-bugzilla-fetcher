import six

import requests as r

from django.conf import settings
from django.contrib.auth.models import get_user_model
from bugs import models

User = get_user_model()


class BugzillaAPI(object):

    # API resources
    AR_BUG = 'bug'
    AR_USER = 'user'
    AR_COMPONENT = 'component'
    AR_PRODUCT = 'product'
    AR_ALL_COMMENTS = 'bug/{bug_id}/comment'
    AR_SPECIFIC_COMMENT = 'bug/comment/{comment_id}'
    AR_GROUP = 'group'
    AR_FLAG_TYPE = 'flag_type'
    AR_CLASSIFICATION = 'classification'
    AR_VERSION = 'version'
    AR_EXTENSIONS = 'extensions'
    AR_TIMEZONE = 'timezone'
    AR_TIME = 'time'
    AR_PARAMETERS = 'parameters'
    AR_LAST_AUDIT_TIME = 'last_audit_time'
    AR_ALL_ATTACHMENTS = 'bug/{bug_id}/attachment'
    AR_SPECIFIC_ATTACHMENT = 'bug/attachment/{attachment_id}'
    AR_RESOURCE_FIELDS = 'field/{resource}'

    def __init__(self, search_terms={}, *args, **kwargs):
        if not search_terms:
            search_terms = {'bug_status': ['__open__'],
                            'limit': ['0'],
                            'list_id': ['175838'],  # TODO
                            'order': ['priority,bug_severity'],
                            'query_format': ['specific']}
        self.search_terms = search_terms
        self.chosen_resource = ''
        self.url_base = settings.BUGZILLA_REST_BASE

    def _get_api_resource_path(self):
        return "{}/{}".format(self.url_base, self.chosen_resource)

    def _get_detail_object_path(self, id):
        return "{}/{}".format(self._get_api_resource_path(), id)

    def fetch_bugs(self, get_params={}):
        self.chosen_resource = self.AR_BUG
        params = self.search_terms
        if get_params:
            params = get_params
        response = r.get(self._get_api_resource_path(), params=params)
        if response.ok:
            try:
                return True, response.json()['bugs']
            except (ValueError, KeyError):
                # In case they send bad data even on HTTP 200 OK
                # OR if `bugs` object is not present in JSON response.
                return False, response.text
        else:
            return False, response

    def _get_users(self, user_details):
        """
        Input can be dict of single user or list of dicts.
        Output will be list of gotten or created users.
        """
        users = []
        if isinstance(user_details, dict):
            user_details = [user_details]
        elif isinstance(user_details, six.string_types):
            user_details = {'email': user_details, 'real_name': user_details}
        for detail in user_details:
            name_parts = user_details['real_name'].partition(' '),
            first_name = name_parts[0],
            last_name = " ".join(name_parts[1:])
            user, _ = User.objects.get_or_create(
                email=user_details['email'],
                first_name=first_name,
                last_name=last_name,
            )
            users.append(user)
        return users

    def _get_bugs(self,  bug_ids, fk=False):
        """
        bug_ids: Can be list or one value.
                if list -> M2M
                else FK
        """
        if isinstance(bug_ids, list):
            return models.Bug.objects.filter(bz_id__in=bug_ids)
        else:
            # filter().first to avoid errors if somehow bug doesn't already exist
            # and to safely return None
            return models.Bug.objects.filter(bz_id=bug_ids).first()

    def _get_non_user_fk_objects(self, input, model):
        return model.objects.get_or_create(name=input)[0]

    def _get_non_user_m2m_objects(self, input_list, model):
        return [model.objects.get_or_create(name=val)[0] for val in input_list]

    def _add_m2m_field_objects(self, bug, aliases, cc, flags, groups, keywords):
        bug.alias.add(aliases)
        bug.cc.add(cc)
        bug.flags.add(flags)
        bug.groups.add(groups)
        bug.keywords.add(keywords)

    def _filter_bugs(self, bz_id_list, single=False):
        if single:
            return models.Bug.objects.filter(bz_id=bz_id_list).first()
        return models.Bug.objects.filter(bz_id__in=bz_id_list)

    def _clear_pending_fk_and_m2m_to_self(self, mapping):
        """
        mapping = {
            <bz_id>: {
                'blocks': [],
                'depends_on': [],
                'see_also': [],
            }
        }

        This func basically does this for all the non-user m2m fields in Bug:
        bug.<m2m_field>.add([list of m2m objects on that field])
        """
        bz_ids = mapping.keys()
        bugs = self._filter_bugs(bz_ids)
        """
        for bug in to_be_cleared_bugs:
            get `field` list of bug ids
                for m2m_bug_id in bug ids;
                    m2m_bug = models.Bug.objects.filter(bz_id=m2m_bug_id)
                    if m2m_bug:
                        add m2m_bug
                    else:
                        m2m_bug = self.fetch_single_bug(m2m_bug_id)
                        add m2m_bug
        """
        for bug in bugs:
            for field in ['blocks', 'depends_on', 'see_also']:
                print("Clearing %s for bug %d" % (field, bug.bz_id))
                # getattr(bug, field).add(*self._filter_bugs(mapping[bug.bz_id][field]))
                field_m2m_bugs = []
                for m2m_bug_id in mapping[bug.bz_id][field]:
                    m2m_bug = models.Bug.objects.filter(bz_id=m2m_bug_id)
                    if m2m_bug:
                        field_m2m_bugs.append(m2m_bug)
                    else:
                        # The recursive rabbit hole
                        m2m_bug_detail = self.fetch_bugs(m2m_bug_id, get_params={'id': m2m_bug_id})
                        m2m_bug = self._create_bug(m2m_bug_detail)
                        field_m2m_bugs.append(m2m_bug)
                        # In worst case scenario, we could see each field having 3-4 bugs
                        # If assuming only 1 field of these 3 would always link to an unsaved bug
                        # and that kept happening for 10 jumps straight, we're looking at 1024 recursions.
                        # We can flatten it out in periodic checks and clearing up in a background task
                        # BUT, that's beyond the scope of this assignment.
                getattr(bug, field).add(*field_m2m_bugs)

    def _already_saved(self, bug_detail):
        """
        Given bugzilla single bug json object, check if it already exists in our database.
        """
        return models.Bug.objects.filter(bz_id=bug_detail['id']).exists()

    def _create_bug(self, bug_detail):
        """
        Given dict of bug details from Bugzilla bugs API,
        this function will create and return the Bug model instance for it.
        """
        bug = None

        """
        Initially had modelled these as FK (dupe_of) and M2Ms,
        Had written a lot of supporting code also, to manage these
        (check _clear_pending_fk_and_m2m_to_self etc)
        But then problem of them not existing on creation, and then
        recursively getting them would be unnecessary time waste for the
        purpose of this assignment. Because that would be long implementation
        requiring another celery task that periodically checks Bug records
        in which these fields should be populated but aren't, and then populate them.
        Not a rabbit hole I want to go down into, as I have lot of pressing issues
        to take care of in the little time I have. Hope this is understandable.
        SO, had to go with postgres specific ArrayField instead, as anyways,
        the point is to simply store and nothing else on top of it, as required.

        # pending_fk_and_m2m_to_self = dict(
        #     blocks=bug_detail['blocks'],
        #     depends_on=bug_detail['depends_on'],
        #     see_also=bug_detail['see_also'],
        # )
        """

        aliases = self._get_non_user_m2m_objects(bug_detail['alias'], models.Alias)
        cc = self._get_users(bug_detail['cc_detail']),
        flags = self._get_non_user_m2m_objects(bug_detail['flags'], models.Flag)
        groups = self._get_non_user_m2m_objects(bug_detail['groups'], models.Group)
        keywords = self._get_non_user_m2m_objects(bug_detail['keywords'], models.Keyword)

        values = dict(
            bz_id=bug_detail['id'],
            assigned_to=self._get_users(bug_detail['assigned_to_detail'])[0],

            blocks=bug_detail['blocks'],
            depends_on=bug_detail['depends_on'],
            dupe_of=bug_detail['dupe_of'],
            see_also=bug_detail['see_also'],

            classification=self._get_non_user_fk_objects(bug_detail['classification'], models.Classification),
            component=self._get_non_user_fk_objects(bug_detail['component'], models.Component),
            creation_time=bug_detail['creation_time'],
            creator=self._get_users(bug_detail['creator_detail'])[0],
            deadline=bug_detail['deadline'],
            is_cc_accessible=bug_detail['is_cc_accessible'],
            is_confirmed=bug_detail['is_confirmed'],
            is_creator_accessible=bug_detail['is_creator_accessible'],
            is_open=bug_detail['is_open'],
            last_change_time=bug_detail['last_change_time'],
            op_sys=self._get_non_user_fk_objects(bug_detail['op_sys'], models.OpSys),
            platform=self._get_non_user_fk_objects(bug_detail['platform'], models.Platform),
            priority=self._get_non_user_fk_objects(bug_detail['priority'], models.Priority),
            product=self._get_non_user_fk_objects(bug_detail['product'], models.Product),
            qa_contact=self._get_users(bug_detail['qa_contact'])[0],
            resolution=bug_detail['resolution'],
            severity=self._get_non_user_fk_objects(bug_detail['severity'], models.Severity),
            status=self._get_non_user_fk_objects(bug_detail['status'], models.Status),
            summary=bug_detail['summary'],
            target_milestone=self._get_non_user_fk_objects(bug_detail['target_milestone'], models.TargetMilestone),
            url=bug_detail['url'],
            version=bug_detail['version'],
            whiteboard=bug_detail['whiteboard'],
        )
        bug = models.Bug.objects.create(**values)
        print("Saved bug %d" % bug.bz_id)
        self._add_m2m_field_objects(bug, aliases, cc, flags, groups, keywords)
        print("Added M2M to bug %d" % bug.bz_id)

        # Set all the fk and m2m relations to self (Bug to Bug) for all the bugs processed above.
        # self._clear_pending_fk_and_m2m_to_self(pending_fk_and_m2m_to_self)

        return bug

    def save_bugs(self, bugs=[]):
        """
        Create the bug as it is, without the FK or M2M.
        While processing through the bug list, keep track of bug ids and their FK/M2M to self
        Save those relations after all bugs have been created.

        `pending_fk_and_m2m_to_self`: This variable will store all the relations of FK and M2M of Bug to self
        Because while creating, it is possible that in the data we get bugs that
        have not been yet created but are present as `blocks` or `depends_on` etc.
        """

        # Process through all bugs fetched
        for bug_detail in self.bugs:
            if not self._already_saved(bug_detail):
                # bug, pending_fk_and_m2m_to_self = self._create_bug(bug_detail)
                self._create_bug(bug_detail)

"""

func to get sample vals for some bug key - z should be the bug json list

import json
with open('/tmp/bugs.json') as f:
    ...:     x = json.load(f)
samplevals = lambda z,key: [z[key] for z in x if z[key]]
"""
