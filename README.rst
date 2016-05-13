PyService-Registry
==================


*PyService-Registry: Simple, Fast and Lightweight Service Registry in pure Python*

:Codename: mJano
:Version: 1.0
:Code: https://github.com/cr0hn/pyservice-registry
:Issues: https://github.com/cr0hn/pyservice-registry/issues/
:Python version: Python 3.4 above
:Author: Daniel Garcia (cr0hn) - @ggdaniel

What's PyService-Registry
-------------------------

PyService Registry is a simple service registry, designed with simplicity and performance in mind.

The service registries are very useful **in microservices** environments.

If you don't really need a complicated and heavy services (like Consul, Docker Swarm or so on) and you don't want a bazooka to kill a fly... maybe this project can help you :)


Features
--------

- Simple usage and design.
- Client and server provided
- Plug&play install
- Storage engines: file oriented NoSQL DB or **MongoDB** for scalable environment.
- High performance.
- API well documented, using Swagger

Install
-------

Install is so easy:

.. code-block:: bash

    # python3.4 -m pip install pyservice-registry

Usage
-----

**Server**

.. code-block:: bash

    # pydiscover-server
    Starting pyService Register in 0.0.0.0:8000

.. note::

    You can show more options typing: ``-h`` option.

API Documentation
-----------------

Once you run the server, you can read the API doc, visiting the URL:

    http://127.0.0.1:8000/apidocs/index.html

.. image:: https://raw.githubusercontent.com/cr0hn/pyservice_registry/master/pyservice_registry/images/api_doc.jpg

What's new?
-----------

Version 1.0.0
+++++++++++++

- First version released

License
-------

PyDiscover is released under BSD licence.
