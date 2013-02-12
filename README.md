Habitbot is a recurring task manager that tries to help you establish habits by
letting you set goals and track the length of your streaks.

Also known as the Jerry Seinfeld "don't break the chain" motivational technique.

Installation
------------

### Prerequisites

You will need the following in order to continue with the installation:

* Python2.7
* pip
* virtualenv

Perform the standard practice for installing prerequisites when a
requirements.txt file is provided:

    $ virtualenv env
    $ . env/bin/activate
    (env)$ pip install -r requirements.txt

###  Configuration

To signify your machine as a development machine (as opposed to a production
machine), place the following in your `~/.bashrc` or `~/.bash_profile` (which
ever you have set to load on a new shell session)

    export DEVELOPMENT=1

Make sure to `$ source ~/.bashrc` or `$ source ~/.bash_profile` so the
DEVELOPMENT environment variable will exist in your current session.

We now need to configure the settings of the Django project. 

1. Copy `habitbot/settings_secret.py.template` to `habitbot/settings_secret.py`.
   Fill in the `ADMINS` and `DATABASES` variables with your preferences. 
2. To obtain a Twitter key pair (used by TWITTER_CONSUMER_KEY and
   TWITTER_CONSUMER_SECRET), visit https://dev.twitter.com/apps. Create a new
   application, and be sure to use `http://127.0.0.1:8000` as the Website and
   Callback URL.
3. To generate a SECRET_KEY, open a python shell and use the output of 

        import os
        import base64
        base64.urlsafe_b64encode(os.urandom(50))
4. If you have signified your machine as a development machine, edit the
   `habitbot/settings_dev.py` file. Adjust the DB_PATH and DATABASES variables
   to fit your preferences.

You should now be able to run the following from the project root

    $ python manage.py syncdb
    $ python manage.py migrate
    $ python manage.py runserver

And we're done!

Troubleshooting the installation
--------------------------------

* If static assets are not showing up, ensure you are actually running in the
  development environment. You should see following upon running the app:

        $ python manage.py runserver
        Running with development settings # Indicates dev environment
        Running with development settings
        Validating models...

        0 errors found
        Django version 1.4.3, using settings 'habitbot.settings'
        Development server is running at http://127.0.0.1:8000/
        Quit the server with CONTROL-C.
* If the application throws a 500 error but all you see is "A server error has
  occurred. Please contact the administrator", then the application is not
  running in development mode. Ensure the DEVELOPMENT environment is set:

        $ echo $DEVELOPMENT
        1
* If you receive a 401 error upon clicking the green sign in button, check for
  the following:
    + Proper Website and Callback URL of `http://127.0.0.1:8000`
    + Make sure you did not accidentally swap the consumer key/consumer secret.
* If you receieve the error 

        sqlite3.OperationalError: unable to open database file
  make sure you have your DB_PATH set correctly in the dev and secret
  configuration files.

