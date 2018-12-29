from celery.schedules import crontab
from celery.decorators import periodic_task

from third_party.bugzilla import BugzillaAPI


@periodic_task(run_every=crontab(minute=0, hour=0))
def fetch_bugzilla_bugs():
    bz = BugzillaAPI()
    success, bugs_or_error = bz.fetch_bugs()
    if success:
        save_count = bz.save_bugs(bugs_or_error)
        print("Saved %d bugs" % save_count)
    else:
        print bugs_or_error
    # TODO -
    # paginated fetching
    # flesh out save to DB
