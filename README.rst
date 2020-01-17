gh_app_starter
--------------

A starter webservice for building a GitHub App using gidgethub, aiohttp, and
deployment to Heroku.

This has been modified to allow the webservice to run on an arbitrary
webserver and install on an arbitrary GitHub Enterprise server.

Webserver Setup
---------------

Python virtualenv
^^^^^^^^^^^^^^^^^
The webserver should run in a separate virtualenv for each GitHub
Enterprise Server installation. Each virtualenv will need to have the
following modules installed (``pip install modulename``):

- aiohttp
- gidgethub
- PyJWT
- cryptography
- cachetools

Alternatively, check the ``requirements.txt`` file in the repository.

Environment variables
^^^^^^^^^^^^^^^^^^^^^

The environment variables for setting up each GitHub Enterprise instance
can be set in the bin/activate file in the Python virtualenv. 

``GH_API_URL``: The base URL for API requests for your GitHub Enterprise
server. Typically, this is something like ``https://servername/api/v3``,
but for github.com it will be ``https://api.github.com``

``GH_SECRET``: The secret key from your GitHub App

``GH_APP_ID``: The ID of your GitHub App

``GH_PRIVATE_KEY``: The private key of your GitHub App. It looks like:

```
-----BEGIN RSA PRIVATE KEY-----
somereallylongtext
-----END RSA PRIVATE KEY-----
```

Heroku Setup
------------


|Deploy|

.. |Deploy| image:: https://www.herokucdn.com/deploy/button.svg
   :target: https://heroku.com/deploy?template=https://github.com/mariatta/gh_app_starter


Add the following config vars in Heroku.

``GH_SECRET``: The secret key from your GitHub App

``GH_APP_ID``: The ID of your GitHub App

``GH_PRIVATE_KEY``: The private key of your GitHub App. It looks like:

```
-----BEGIN RSA PRIVATE KEY-----
somereallylongtext
-----END RSA PRIVATE KEY-----
```
