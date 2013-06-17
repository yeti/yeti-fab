Yeti's Fabric File
==================

yeti-fab is a [fabric script](http://docs.fabfile.org/en/1.6/) to start [Django](https://www.djangoproject.com/) projects at [Yeti LLC](http://www.yetihq.com/python-django/).

Check our blog article written at http://www.yetihq.com/blog/beginner-devops-with-django-and-fabric/ in the meantime before we document the script here.

Prerequisites
-------------

You will need the following configured before using yeti-fab:

* Mac OS X (Linux or UNIX is currently in testing)
** XCode
** XCode Developer Tools
* python (should be installed with pip)
* git
* [fabric](http://docs.fabfile.org/en/1.6/)
* virtualenv 
* MySQL or Postgresql

Setup
------

* Install [Homebrew pacakage manager](https://python-guide.readthedocs.org/en/latest/starting/install/osx/) for Mac OS X.
  Homebrew will help to install python. Run: `ruby -e "$(curl -fsSkL raw.github.com/mxcl/homebrew/go)"`

* Python should be installed on your computer using Homebrew.

* Fabric must be installed:

        `pip install fabric`

Commands
--------

### Configuration

Configure the base operating system. Mac is the default supported OS.

        fab linux <other commands...>
        fab unix <other commands...>
        fab mac <other commands...>

Configure the database. Postgresql is the default supported database.

        fab postgresql <other commands...>
        fab mysql <other commands...>

### Mezzanine Projects

Install OS prerequisites:

        fab installdb

Create a project:

        fab new:<virtual_env_name>,<project_name>,<app_name>[,<db_password>]

Clone an existing Yeti project (you must be authorized):

        fab clone:<virtual_env_name>,<project_name>[,<db_password>]

Remove a local project:

        fab remove:<project_name>,[<db_password>]
        fab removedb:<project_name>,[<db_password>]

### RabbitMQ

Install OS prerequisites:

        fab installrabbit

Add a RabbitMQ user:

        fab addrabbit:<user>,<password>,<virtualhost>

Remove a RabbitMQ user:

        fab removerabbit:<user>,<virtualhost>

Monitor RabbitMQ:

        fab rabbitmonitor:on,<user>
        fab rabbitmonitor:off,<user>
