Yeti's Fabric File
==================

yeti-fab is a [fabric script](http://docs.fabfile.org/en/1.6/) to start [Django](https://www.djangoproject.com/) projects at [Yeti LLC](http://www.yetihq.com/python-django/).

Check our blog article written at http://www.yetihq.com/blog/beginner-devops-with-django-and-fabric/ in the meantime before we document the script here.

Prerequisites
-------------

You will need the following configured before using yeti-fab:

* Mac OS X
* XCode
* XCode Developer Tools
* python (should be installed with pip)
* [fabric](http://docs.fabfile.org/en/1.6/)
* virtualenv 
* MySQL
* git

Setup
------

* Install [Homebrew pacakage manager](https://python-guide.readthedocs.org/en/latest/starting/install/osx/) for Mac OS X. Homebrew will help to install python. Run: `ruby -e "$(curl -fsSkL raw.github.com/mxcl/homebrew/go)"`

* Python should be installed on your computer using Homebrew.

* Fabric must be installed:

        `pip install fabric`

* Install dependencies for your project. We have several dependencies supported.

** RabbitMQ. `fab rabbitmq`

Commands
--------

### Projects

Creating a project:

    fab new:<virtual_env_name>,<project_name>,<app_name>[,<db_password>]

Cloning an existing Yeti project (you must be authorized):

    fab clone:<virtual_env_name>,<project_name>[,<db_password>]

Removing a local project:

    fab remove:<project_name>,[<db_password>]
    fab removedb:<project_name>,[<db_password>]

### RabbitMQ configuration

Adding a RabbitMQ user:

        fab addrabbit:<user>,<password>,<virtualhost>

Removing a RabbitMQ user:

        fab removerabbit:<user>,<virtualhost>

RabbitMQ monitoring:

        fab rabbitmonitor:on,<user>
        fab rabbitmonitor:off,<user>
