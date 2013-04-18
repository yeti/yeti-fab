Yeti's Fabric File
==================

yeti-fab is a [fabric script](http://docs.fabfile.org/en/1.6/) to start Python Django projects at [Yeti LLC](http://www.yetihq.com/python-django/) quickly.

Check our blog article written at http://www.yetihq.com/blog/beginner-devops-with-django-and-fabric/ in the meantime before we document the script here.

Prerequisites
-------------

You will need the following configured before using yeti-fab:

* Mac OS X (Linux untested)
* XCode Developer Tools (Mac OS X only)
* [Homebrew installation of Python 2.7](https://python-guide.readthedocs.org/en/latest/starting/install/osx/)
    * virtualenv 
    * [fabric](http://docs.fabfile.org/en/1.6/)
    * pip
* MySQL
* git

Commands
--------

Creating a project:

    fab new:<virtual_env_name>,<project_name>,<app_name>[,<db_password>]

Cloning an existing Yeti project (you must be authorized):

    fab clone:<virtual_env_name>,<project_name>[,<db_password>]

Removing a local project:

    fab remove:<project_name>,[<db_password>]
    fab removedb:<project_name>,[<db_password>]

