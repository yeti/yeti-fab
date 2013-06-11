import subprocess
from fabric.context_managers import prefix, lcd, settings
from fabric.operations import os, _AttributeString, _prefix_commands, _prefix_env_vars, prompt
from fabric.state import output, win32
from fabric.utils import error
from os.path import exists
from fabric.colors import *

class Helper:
    def add_line_to_list(self, read_file, write_file, list, insert_line):
        f = open(read_file, "r")
        g = open(write_file, "w")

        state = 0 
        # 0 - beginning of file
        # 1 - inside the list
        # 2 - after the list

        line = f.readline()
        while len(line) > 0: # a zero-length line defines end of file
            if state == 0:
                if line.find(list) == 0: # identified the start list
                    state = 1
            elif state == 1:
                if line.find(")") == 0: # identified the end list
                    # add in the inserted line here
                    g.write("%s\n" % insert_line)
                    state = 2

            # write the line as is
            g.write(line)

            # read the next line
            line = f.readline()

        g.close()
        f.close()

def homebrew():
    """
    Installs homebrew
    """
    bash_local('ruby -e "$(curl -fsSkL raw.github.com/mxcl/homebrew/go)"')

def rabbitmq():
    """
    Installs rabbitmq, requires homebrew
    """
    bash_local("brew update")
    bash_local("brew doctor")
    bash_local("brew install rabbitmq")

    with open("/etc/paths","r") as f:
        file = f.read()
        f.close()
        if file.find("/usr/local/sbin") != -1:
            bash_local("sudo echo /usr/local/sbin >> /etc/paths")


    print("To start rabbitmq: rabbitmq-server")

def addrabbit(user, password, virtualhost):
    """
    Adds a rabbit user, assumes that rabbitmq is installed
    """
    bash_local("sudo rabbitmqctl add_user %s %s" % (user, password))
    bash_local("sudo rabbitmqctl add_vhost %s" % virtualhost)
    bash_local('sudo rabbitmqctl set_permissions -p %s %s ".*" ".*" ".*"' % (virtualhost, user))

def removerabbit(user, virtualhost):
    """
    Removes a rabbit user
    """
    bash_local("sudo rabbitmqctl delete_user %s" % user)
    bash_local("sudo rabbitmqctl delete_vhost %s" % virtualhost)

def rabbitmonitor(enable,user=""):
    """
    Enables rabbitmq monitoring, optionally taking a username to enable for the control panel
    """
    if enable=="yes" or enable=="on":
        bash_local("rabbitmq-plugins enable rabbitmq_management")
        if len(user):
            bash_local("sudo rabbitmqctl set_user_tags %s administrator" % user)
        print "Running on http://localhost:15672"
    else:
        bash_local("rabbitmq-plugins disable rabbitmq_management")
        if len(user):
            bash_local("sudo rabbitmqctl set_user_tags %s" % user)

def testdb(db_password=''):
    """
    Test that the password is valid for the user 'root' on the local computer.
    """

    # guard against space in password
    if db_password.find(" ") >= 0:
        print red("This script doesn't work when passwords contain spaces.")
        return False

    # guard against script injection
    if db_password.find("\n") >= 0:
        print red("Stopping, prevent script injection in password.")
        return False

    with prefix('export PATH="$PATH:/usr/local/mysql/bin/"'):
        out = None

        with settings(warn_only=True):
            # verify that the mysqladmin tool is installed correctly
            out = bash_local("mysqladmin --version")

            if not out.succeeded:
                print red("You need to install mysql before running this script")
                return False

            # test the password is valid
            if len(db_password) > 0:
                out = bash_local("mysqladmin --user=root --password=%s debug" % (db_password,))
            else:
                out = bash_local("mysqladmin --user=root debug")

            if not out.succeeded:
                print red("The password you provided is invalid")
                return False

            return out.succeeded


#TODO: Check if virtualenv, project directory, or database already exists - then we should prompt for skip/fail/quit
#TODO: If the script fails should we rollback (delete) the virtualenv, project directory, and database?
#TODO: We could test and fail gracefully for dependencies (virtualenvwrapper, pip, mysql)
def new(virtual_env_name='', project_name='', app_name='', db_password=''):
    """
    Sets up a new mezzanine-django project using virtualenvwrapper, mysql, and pip with an unfuddle repository
    """
    if len(virtual_env_name) == 0 or len(project_name) == 0 or len(app_name) == 0:
        print "Usage: fab new:<virtual_env_name>,<project_name>,<app_name>[,<db_password>]"
        print ""
        print "Assumptions: db_username = 'root'"
        print "             db_password = '' if <db_password> is not specified"
        print "             db_password is for the local user only"
        print ""
        print "Common usage:"
        print "            <virtual_env_name> == <project_name>"
        print "            <project_name> should be different than <app_name>"
        return

    # ensure the database has been set up correctly
    if not testdb(db_password):
        return

    # check to make sure that the environment name and project name are the same
    if virtual_env_name != project_name:
        question = prompt("Usually the virtual environment (virtualenv) name should be the same as the project_name. Do you want to continue this script (Y/[N])?",validate="^[YyNn]?$")
        if not (question == 'y' or question == 'Y'):
            return

    # ensure that project_name and app_name are different
    if project_name == app_name:
        question = prompt("Your app_name is the same as the project_name. They should be different. Continue? (Y/[N])?",validate="^[YyNn]?$")
        if not (question == 'y' or question == 'Y'):
            return

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
                    bash_local("echo 'MEDIA_URL = \"http://127.0.0.1:8000/static/media/\"' >> local_settings.py")
                    bash_local("cp local_settings.py local_settings.py.template")

                    # modify the password after creating the template file, we don't check in the password as the template (each user has different settings)
                    bash_local("sed 's/\"PASSWORD\": \"\"/\"PASSWORD\": \""+ db_password + "\"/g' local_settings.py > local_settings.py.tmp")
                    bash_local("mv local_settings.py.tmp local_settings.py")

                    bash_local("chmod +x manage.py")
                    bash_local("pip freeze > requirements/requirements.txt")
                    bash_local("./manage.py startapp %s" % app_name)

                    # let's access the settings file, output.succeeded should contain the working directory
                    output = bash_local("pwd", capture=True)
                    h = Helper()
                    h.add_line_to_list(output + "/settings.py", output + "/settings.py.tmp", "INSTALLED_APPS = (", '    "%s",' % app_name)
                    bash_local("mv settings.py.tmp settings.py")                        

                    with prefix('export PATH="$PATH:/usr/local/mysql/bin/"'):
                        if len(db_password) > 0:
                            bash_local("mysqladmin -u root --password=%s create %s" % (db_password, virtual_env_name))
                        else:
                            bash_local("mysqladmin -u root create %s" % virtual_env_name)
                    bash_local("./manage.py syncdb")

                    bash_local("./manage.py schemamigration %s --initial" % app_name)
                    bash_local("./manage.py migrate")

                    bash_local("git init")
                    bash_local("echo '.idea/' >> .gitignore")
                    bash_local("git add .")
                    bash_local("git commit -m'init'")

                    #TODO: Tie to Unfuddle?

#TODO: project_name must be known from the git repository
def clone(virtual_env_name="", project_name="", db_password=""):
    """
    Clones a new mezzanine-django project using virtualenvwrapper, mysql, and pip from an unfuddle git repository
    """
    if len(virtual_env_name) == 0 or len(project_name) == 0:
        print "Usage: fab clone:<virtual_env_name>,<project_name>[,<db_password>]"
        print ""
        print "Assumptions: db_username = 'root'"
        print "             db_password = '' if <db_password> is not specified"
        print "             db_password is for the local user only"
        print ""
        print "Common usage: <virtual_env_name> == <project_name>"
        return

    if not testdb(db_password):
        return 

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

                # modify the password after creating the template file, we don't check in the password as the template (each user has different settings)
                bash_local("sed 's/\"PASSWORD\": \"\"/\"PASSWORD\": \""+ db_password + "\"/g' local_settings.py > local_settings.py.tmp")
                bash_local("mv local_settings.py.tmp local_settings.py")


                #TODO: assumes you're using root user and has no password, we should prompt for this
                with prefix('export PATH="$PATH:/usr/local/mysql/bin/"'):
                    if len(db_password) > 0:
                        bash_local("mysqladmin -u root --password=%s create %s" % (db_password, virtual_env_name))
                    else:
                        bash_local("mysqladmin -u root create %s" % virtual_env_name)

                bash_local("./manage.py syncdb")
                bash_local("./manage.py migrate")


def remove(project_name, db_password=""):
    """
    Remove an existing project on your computer. 
    WARNING: This script will not back up your source code before deletion.

    Usage:
        remove:<project_name> 
        remove:<project_name>,<db_password>
    """

    # check for the database
    if not testdb(db_password):
        return

    with prefix("source ~/.bash_profile"):
        # check to see if the virtual env has been fully removed, not removed because of compiled stuff
        bash_local("rmvirtualenv %s" % project_name)
        workon_home = os.getenv('WORKON_HOME')
        
        if exists("%s/%s" % (workon_home, project_name)):
            bash_local("sudo rm -rf %s/%s" % (workon_home, project_name))

        # remove the source code directory
        if exists("%s/%s/.git" % (project_name, project_name)):
            question = prompt("Do you want to remove the local copy of `%s` (Y/[N])?" % project_name,validate="^[YyNn]?$")
            if not (question == 'y' or question == 'Y'):
                return

            bash_local("rm -rf %s/%s/.git" % (project_name,project_name))
            bash_local("rm -r %s" % project_name)
        elif exists("%s/.git" % project_name):
            question = prompt("Do you want to remove the local copy of `%s` (Y/[N])?" % project_name,validate="^[YyNn]?$")
            if not (question == 'y' or question == 'Y'):
                return

            bash_local("rm -rf %s/.git" % project_name)
            bash_local("rm -r %s" % project_name)
        elif exists("%s" % project_name):
            question = prompt("Do you want to remove the only copy of `%s` from your computer (Y/[N])?" % project_name,validate="^[YyNn]?$")
            if not (question == 'y' or question == 'Y'):
                return
            
            bash_local("rm -r %s" % project_name)


        # don't remove the database but tell the user
        with prefix('export PATH="$PATH:/usr/local/mysql/bin/"'):
            with settings(warn_only=True):
                if len(db_password):
                    cmd = "mysql -u root --password=%s -e 'use %s'" % (db_password,project_name)
                else:
                    cmd = "mysql -u root -e 'use %s'" % project_name
                output = bash_local(cmd)

                # don't actually remove the database for now
                if output.succeeded:
                    print yellow("Your database still exists. You should remove it manually by calling\n removedb:%s,<db_password>" % project_name)

def removedb(project_name, db_password=""):
    """
    Remove an existing database from your computer that corresponds to a project.
    """

    if not testdb(db_password):
        return

    with prefix('export PATH="$PATH:/usr/local/mysql/bin/"'):
        with prefix("source ~/.bash_profile"):
            if len(db_password):
                cmd = "mysqladmin -u root --password=%s drop %s" % (db_password,project_name)
            else:
                cmd = "mysqladmin -u root drop %s" % project_name
            output = bash_local(cmd)


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