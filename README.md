# README

## About

This was an assignment for an interview. Problem statement:

> *You need to fetch all the bugs from "https://bz.apache.org/bugzilla/index.cgi" and store the in any database of your choice.*

## Installation

1. Clone the repo:
```
git clone https://github.com/noodlebreak/bugzilla.git
cd bugzilla
mkvirtualenv bugzilla
```
And run `pip install -r requirements/dev.txt` to install Python dependencies.

2. Create PostgreSQL database:
`createdb <db_name>`

3. Create a `conf.ini` file using the given `conf.ini.sample` file the project app `bugzilla`, along side `settings.py`

4. Enter database credentials in it.

5. Run `./manage.py migrate` in project root dir.

6. Open up django shell: `./manage.py shell_plus` and execute accordingly:
    - If you want to run the import in background using celery:
        + Run a celery node in another terminal tab:  
            `celery -A bugzilla worker -B -c1 -linfo`
        + Execute this from shell:
            `from bugs import tasks; tasks.fetch_bugzilla_bugs.delay()`
    - Else if you are okay with directly running import in the shell, execute this in the shell:
        `from bugs import tasks; tasks.fetch_bugzilla_bugs()`

You can then check the bugs imported in either admin by running Django local server: `./manage.py runserver` and opening this in the browser: [http://localhost:8000/admin/](http://localhost:8000/admin/) and logging in with a staff/superuser account.

NOTE: You need to have created a superuser to log into admin, so run this in terminal in project root dir: `./manage.py createsuperuser` and follow the instructions.

All commands in case your `virtualenvwrapper` and PostgreSQL is all setup:

```
git clone https://github.com/noodlebreak/bugzilla.git
cd bugzilla
mkvirtualenv bugzilla
pip install -r requirements/dev.txt
createdb bugzilla
./manage.py migrate
```

## Sample Run Screenshot:

![Locally run on celery](https://i.imgur.com/BuwVPCg.png)