import subprocess
from fabric.context_managers import prefix, lcd
from fabric.operations import os, _AttributeString, _prefix_commands, _prefix_env_vars
from fabric.state import output, win32
from fabric.utils import error

#TODO: Check if virtualenv, project directory, or database already exists - then we should prompt for skip/fail/quit
#TODO: If the script fails should we rollback (delete) the virtualenv, project directory, and database?
#TODO: We could test and fail gracefully for dependencies (virtualenvwrapper, pip, mysql)
def new(virtual_env_name, project_name, app_name, db_password=''):
    """
    Sets up a new mezzanine-django project using virtualenvwrapper, mysql, and pip with an unfuddle repository
    """
    with prefix("source ~/.bash_profile"):
        bash_local("mkvirtualenv %s" % virtual_env_name)
        bash_local("mkdir %s" % project_name)
        with lcd("%s" % project_name):
            with prefix("workon %s" % virtual_env_name):
                bash_local("sudo pip install mezzanine")
                bash_local("mezzanine-project %s" % project_name)
                bash_local("sudo pip install south")

                #TODO: This line makes assumptions that we're using macbooks, exporting the path may not break anything on other machines though
                #Add mysql_config to the path temporarily so mysql-python installs correctly
                with prefix('export PATH="$PATH:/usr/local/mysql/bin/"'):
                    bash_local("sudo pip install mysql-python")

                with lcd("%s" % project_name):
                    #TODO: Create a function for copying and moving the file
                    bash_local("sed 's/backends.sqlite3/backends.mysql/g' local_settings.py > local_settings.py.tmp")
                    bash_local("mv local_settings.py.tmp local_settings.py")
                    bash_local("sed 's/dev.db/%s/g' local_settings.py > local_settings.py.tmp" % virtual_env_name)
                    bash_local("mv local_settings.py.tmp local_settings.py")
                    bash_local("sed 's/\"USER\": \"\"/\"USER\": \"root\"/g' local_settings.py > local_settings.py.tmp")
                    bash_local("mv local_settings.py.tmp local_settings.py")
                    bash_local("sed 's/\"PASSWORD\": \"\"/\"PASSWORD\": \""+ db_password + "\"/g' local_settings.py > local_settings.py.tmp")
                    bash_local("mv local_settings.py.tmp local_settings.py")
                    bash_local("echo 'MEDIA_URL = \"http://127.0.0.1:8000/static/media/\"' >> local_settings.py")
                    bash_local("cp local_settings.py local_settings.py.template")

                    bash_local("chmod +x manage.py")
                    bash_local("pip freeze > requirements/requirements.txt")
                    bash_local("./manage.py startapp %s" % app_name)
                    #TODO: Add new app to installed_apps
                    #Issue is putting in a new line before the added text with sed
                    #Potentially could use awk instead
                    #                    command = '''sed 's/INSTALLED_APPS = (/&\
                    #                        "%s",/g' settings.py > settings.py.tmp
                    #                    ''' % app_name
                    #                    bash_local(command)
                    #                    bash_local("sed 's/INSTALLED_APPS = (/&\
                    #                        \"%s\",/g' settings.py > settings.py.tmp" % app_name)
                    #                    bash_local("mv settings.py.tmp settings.py")

                    #TODO: assumes you're using root user and has no password, we should prompt for this
                    with prefix('export PATH="$PATH:/usr/local/mysql/bin/"'):
                        if len(db_password) > 0:
                            bash_local("mysqladmin -u root --password=%s create %s" % (db_password, virtual_env_name))
                        else:
                            bash_local("mysqladmin -u root create %s" % virtual_env_name)
                    bash_local("./manage.py syncdb")

                    #TODO: Put this back in once we figure out adding new app to installed_apps
                    #                    bash_local("./manage schemamigration %s --initial" % app_name)
                    bash_local("./manage.py migrate")

                    bash_local("git init")
                    bash_local("echo '.idea/' >> .gitignore")
                    bash_local("git add .")
                    bash_local("git commit -m'init'")

                    #TODO: Tie to Unfuddle?

#TODO: project_name must be known from the git repository
def clone(virtual_env_name, project_name):
    """
    Clones a new mezzanine-django project using virtualenvwrapper, mysql, and pip from an unfuddle git repository
    """
    with prefix("source ~/.bash_profile"):
        bash_local("mkvirtualenv %s" % virtual_env_name)
        bash_local("git clone git@yeti.unfuddle.com:yeti/%s.git" % project_name)
        with lcd("%s" % project_name):
            with prefix("workon %s" % virtual_env_name):
                #TODO: This line makes assumptions that we're using macbooks, exporting the path may not break anything on other machines though
                #Add mysql_config to the path temporarily so mysql-python installs correctly
                with prefix('export PATH="$PATH:/usr/local/mysql/bin/"'):
                    bash_local("sudo pip install -r requirements/requirements.txt")

                bash_local("cp local_settings.py.template local_settings.py")

                #TODO: assumes you're using root user and has no password, we should prompt for this
                with prefix('export PATH="$PATH:/usr/local/mysql/bin/"'):
                    bash_local("mysqladmin -u root create %s" % virtual_env_name)
                bash_local("./manage.py syncdb")
                bash_local("./manage.py migrate")

#TODO: If fabric updates the local() function we won't get the benefits unless we re-copy the function
# This is a copy of fab's local() that uses bash instead of sh
def bash_local(command, capture=False):
    """
    Run a command on the local system.

    `local` is simply a convenience wrapper around the use of the builtin
    Python ``subprocess`` module with ``shell=True`` activated. If you need to
    do anything special, consider using the ``subprocess`` module directly.

    `local` is not currently capable of simultaneously printing and
    capturing output, as `~fabric.operations.run`/`~fabric.operations.sudo`
    do. The ``capture`` kwarg allows you to switch between printing and
    capturing as necessary, and defaults to ``False``.

    When ``capture=False``, the local subprocess' stdout and stderr streams are
    hooked up directly to your terminal, though you may use the global
    :doc:`output controls </usage/output_controls>` ``output.stdout`` and
    ``output.stderr`` to hide one or both if desired. In this mode,
    `~fabric.operations.local` returns None.

    When ``capture=True``, this function will return the contents of the
    command's stdout as a string-like object; as with `~fabric.operations.run`
    and `~fabric.operations.sudo`, this return value exhibits the
    ``return_code``, ``stderr``, ``failed`` and ``succeeded`` attributes. See
    `run` for details.

    `~fabric.operations.local` will honor the `~fabric.context_managers.lcd`
    context manager, allowing you to control its current working directory
    independently of the remote end (which honors
    `~fabric.context_managers.cd`).

    .. versionchanged:: 1.0
        Added the ``succeeded`` and ``stderr`` attributes.
    .. versionchanged:: 1.0
        Now honors the `~fabric.context_managers.lcd` context manager.
    .. versionchanged:: 1.0
        Changed the default value of ``capture`` from ``True`` to ``False``.
    """
    given_command = command
    # Apply cd(), path() etc
    wrapped_command = _prefix_commands(_prefix_env_vars(command), 'local')
    if output.debug:
        print("[localhost] local: %s" % (wrapped_command))
    elif output.running:
        print("[localhost] local: " + given_command)
        # Tie in to global output controls as best we can; our capture argument
    # takes precedence over the output settings.
    dev_null = None
    if capture:
        out_stream = subprocess.PIPE
        err_stream = subprocess.PIPE
    else:
        dev_null = open(os.devnull, 'w+')
        # Non-captured, hidden streams are discarded.
        out_stream = None if output.stdout else dev_null
        err_stream = None if output.stderr else dev_null
    try:
        cmd_arg = wrapped_command if win32 else [wrapped_command]
        p = subprocess.Popen(cmd_arg, shell=True, stdout=out_stream,
            stderr=err_stream, executable="/bin/bash")
        (stdout, stderr) = p.communicate()
    finally:
        if dev_null is not None:
            dev_null.close()
        # Handle error condition (deal with stdout being None, too)
    out = _AttributeString(stdout.strip() if stdout else "")
    err = _AttributeString(stderr.strip() if stderr else "")
    out.failed = False
    out.return_code = p.returncode
    out.stderr = err
    if p.returncode != 0:
        out.failed = True
        msg = "local() encountered an error (return code %s) while executing '%s'" % (p.returncode, command)
        error(message=msg, stdout=out, stderr=err)
    out.succeeded = not out.failed
    # If we were capturing, this will be a string; otherwise it will be None.
    return out