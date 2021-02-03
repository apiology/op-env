======
op-env
======


.. image:: https://circleci.com/gh/apiology/op_env.svg?style=svg
    :target: https://circleci.com/gh/apiology/op_env

.. image:: https://img.shields.io/pypi/v/op_env.svg
        :target: https://pypi.python.org/pypi/op_env

.. image:: https://readthedocs.org/projects/op-env/badge/?version=latest
        :target: https://op-env.readthedocs.io/en/latest/?badge=latest
        :alt: Documentation Status

* Free software: MIT license
* Documentation: https://op-env.readthedocs.io.


Features
--------

op-env allows you to use 1Password entries as environment variable-style secrets.  This makes it easier to rotate secrets in places where the source of truth is 1Password.

You can use op-env by setting your desired environment variable name as a tag in the 1Password entry that you want to use.

Q&A
---

**How do I install op-env?**

1. You'll first need to install and configure the `"op" CLI from 1Password <https://support.1password.com/command-line-getting-started/>`_.  I personally use ``brew install 1password-cli`` for that.
2. To make using that a little less painful, I wrote  `with-op`_, which will stash your op temporary key in your system's keychain so you don't need to fiddle around with your environment.  Your choice, though!  Install using pip.  ``python3 -m pip install with_op``
3. Install using pip.  ``python3 -m pip install op_env``

**How do I run it?**

Let's say you have a web server you're running locally named ``web-server``.  Let's pass in environment variables pointing to the database it should connect to.

1. Find or create your 1Password entry.  Make sure the server, port, username and password are there, with those strings as the keys in the 1Password entry (this lines up with the 'Server' category if you want to use that!)

2. Edit the entry and add tags for the env variable that your web server uses.  Let's say they're called ``WEB_DB_SERVER``, ``WEB_DB_PORT``, ``WEB_DB_USERNAME``, ``WEB_DB_PASSWORD`` - so add four tags.

3. Run your server with ``with-op op-env run -e WEB_DB_SERVER -e WEB_DB_PORT -e WEB_DB_USERNAME -e WEB_DB_PASSWORD web-server``

4. Smile with the smug satisfaction of someone who doesn't have yet another password hanging around in a text file on disk.

**Which field does op-env read?  Can I pull a username, password, servername and port from 1Password?**

op-env uses the name of the env variable to infer which field in the entry should be used - e.g., 'server' for ``WEB_DB_SERVER``.  It tries to handle common synonyms (more welcome in PRs!) like 'user' for 'username'.  If all else fails it'll pull the 'password' field.

**What if the env variable naming doesn't line up with the field in 1Passsword?**

Right now your best bet is to either duplicate the field in 1Password with the new name, rename the field in 1Password, or rename the env variable.

If you'd like to PR this and add a feature to add a mapping somewhere, file an issue and let's talk.

**What if I have more than one environment?**

In the future I could imagine having some new flag that down-selects by requiring a certain tag (e.g., ``web-server-prod``) or perhaps vault be applied to the 1Password entry to downselect to the right set of entries.  File an issue if you're interested in taking this on!

**I want something like this, but as something which populates Heroku/Kubernetes/etc.**

That's not a question.  But yeah, I'd definitely imagine these as an extension here - something like ``op-env k8s -e WEB_DB_SERVER`` that creates a secret.

For now, you can use ``op-env json -e WEB_DB_SERVER`` and write a script to process the JSON that it puts out on stdout into what you need.  For that matter, you could write a script (maybe an ERB/jinja template?) that pastes in env variables and run it with ``op-env run``.

**This isn't quite the problem I'm facing.  Are there other things out there that are related I should know about?**

Some pointers to things that might be helpful:

1. `db-facts <https://github.com/bluelabs/db-facts>`_ specializes on setting database information, and integrates well with LastPass (but not yet 1Password).  I wrote this.
2. `op <https://support.1password.com/command-line-getting-started/>`_ is a CLI tool for interacting with 1Password.  It's pretty good, but requires you stash a temporary token in your environment.
3. `with-op`_ helps by stashing that token in your system keychain so you don't need to create wacky shell aliases or whatever.  I wrote this.
4. `lastpass-cli <https://github.com/lastpass/lastpass-cli>`_ is a CLI tool for interacting with LastPass.  It is cruddy and not well-maintained, but it's what's available and is the basis for LastPass support in db-facts.

Credits
-------

This package was created with Cookiecutter_ and the `audreyr/cookiecutter-pypackage`_ project template.

.. _Cookiecutter: https://github.com/audreyr/cookiecutter
.. _`audreyr/cookiecutter-pypackage`: https://github.com/audreyr/cookiecutter-pypackage
.. _`with-op`: https://github.com/apiology/with_op
