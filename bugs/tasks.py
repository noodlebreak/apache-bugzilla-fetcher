import json

from celery.schedules import crontab
from celery.decorators import periodic_task
from bugzilla.celery import app

from third_party.bugzilla import BugzillaAPI

# @periodic_task(run_every=crontab(minute=0, hour=0))


@app.task()
def fetch_bugzilla_bugs():
    bz = BugzillaAPI()
    # success, bugs_or_error = bz.fetch_bugs()
    success = True
    with open("/tmp/bugs.json") as f:
        bugs_or_error = json.load(f)['bugs']
    if success:
        save_count = bz.save_bugs(bugs_or_error)
        print("Saved %d bugs" % save_count)
    else:
        print bugs_or_error
    # TODO -
    # paginated fetching using limit and offset
