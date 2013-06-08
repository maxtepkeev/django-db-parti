Django DB Parti
===============

Django DB Parti is a package for Django which aim is to make table partitioning on the fly.
Partitioning is a division of one large table into smaller tables which represent that table.
Partitioning is usually done for manageability, performance or availability reasons. If you
are unsure whether you need partitioning or not, then you almost certainly don't need it.

Requirements
------------

* Django 1.5 (http://www.djangoproject.com) (may work with older versions, but untested)

Installation
------------

From pypi_::

    $ pip install django-db-parti

or clone from github_::

    $ git clone git://github.com/maxtepkeev/django-db-parti.git

Configuration
-------------

Add dbparti to PYTHONPATH and installed applications::

    INSTALLED_APPS = (
        ...
        'dbparti'
    )

Create the model as usual which will represent the partitioned table, if you are using South
for migrations, you can also create the model as usual. No additional steps required. After that
we need to make a few changes to the model:

\1) In models.py add the following import statement at the top of the file::

    from dbparti.models import Partitionable

\2) Make your model to inherit from Partitionable, to do that change::

    class YourModelName(models.Model):

to::

    class YourModelName(Partitionable):

\3) Optionally add a Meta class to your model with a few settings (or if you already have a Meta class change it as the following)::

    class Meta(Partitionable.Meta):
        partition_range = 'month'
        partition_column = 'partdate'

\4) Lastly we need to initialize some database stuff, to do that execute the following command::

    python manage.py partition app_name

That's it! Easy right?! Now a few words about what we just did. We made our model to inherit from Partitionable, also we
used "month" as partition range and "partdate" as partition column, that means that from now on, a new partition will be
created every month and a value from partdate column will be used to determine into what partition the data should be saved.
Keep in mind that if you add new partitioned models to your apps or change any settings in the existing partitioned models,
you need to rerun the command from step 4, otherwise the database won't know about your changes. You can also customize how
data from that model will be displayed in the Django admin interface, for that you need to do the following:

\1) In admin.py add the following import statement at the top of the file::

    from dbparti.admin import PartitionableAdmin

\2) Create admin model as usual and then change::

    class YourAdminModelName(admin.ModelAdmin):

to::

    class YourAdminModelName(PartitionableAdmin):

\3) Optionally add a setting which tells how records are displayed in Django admin interface (more on that below)::

    partition_show = 'all'

Available settings
------------------

Model settings:
~~~~~~~~~~~~~~~

All model settings are done inside model's Meta class which should inherit from Partitionable.Meta

``partition_range`` - how often a new partition will be created, currently accepts the following:

* week
* month (default)

``partition_column`` - column name, which value will be used to determine which partition record belongs to:

* partdate (default)

ModelAdmin settings:
~~~~~~~~~~~~~~~~~~~~

All model admin settings are done inside model admin class itself

``partition_show`` - data from which partition will be shown in Django admin, the following values are possible:

* all (default)
* current
* previous

Example
-------

Let's imagine that we would like to create a table for storing log files. Without partitioning our table would have
millions of rows very soon and as the table grows performance will become slower. With partitioning we can tell database
that we want a new table to be created every month and that we will use a value from partdate to determine to which partition
every new record belongs to. To be more specific let's call our table "logdata", it will have only 3 columns: id, content and
logdate. Now when we insert the following record: id='1', content='blablabla', logdate='2013-05-20', this record will be
inserted not to our "logdata" table but to the "logdata_y2013m05", then if we insert another record like that: id='2',
content='yadayadayada', logdate='2013-07-16' it will be inserted to the table "logdata_y2013m07" BUT the great thing about
all of that is that you are doing your inserts/updates/selects to the table "logdata"! Again, your are working with the table
"logdata" as usual and you don't may even know that actually your data is stored in a lot of different tables, everything is
done for you automatically at the database level, isn't that cool ?!

Backends
--------

Django DB Parti is designed in a modular way, so new db backends can be added easily, currently the following backends are available:

* postgresql

Limitations
-----------

\1) Partitioning is only possible on a date or datetime basis, so you can't partition for example by ZIP code or something else.
Other partitioning options will be added in next releases.
\2) Partitioning is not available for bulk inserts (i.e. Django's bulk_create() method) becouse it doesn't call model's save()
method which Django DB Parti relies on.
\3) Perhaps there are more limitations that I'm not aware of, if you find any - let me know.

Contact & Support
-----------------

I will be glad to get your feedback, pull requests, issues, whatever. Feel free to contact me for any questions.

Copyright & License
-------------------

``django-db-parti`` is protected by BSD licence.

.. _pypi: https://pypi.python.org/pypi/django-db-parti
.. _github: https://github.com/maxtepkeev/django-db-parti
