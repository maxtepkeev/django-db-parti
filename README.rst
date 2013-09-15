Django DB Parti
===============

Django DB Parti is a package for Django which aim is to make table partitioning on the fly. Partitioning is a
division of one large table into several smaller tables which represent that table. Partitioning is usually
done for manageability, performance or availability reasons. If you are unsure whether you need partitioning
or not, then you almost certainly don't need it.

.. contents:: Table of contents:

Features
--------

Django DB Parti supports multiple database backends, each database differ from each other in many ways, that
means that some features may be available for one database backend, but not for the other, below you will find
list of supported database backends and detailed information which database backend supports which features.

PostgreSQL
~~~~~~~~~~

Implementation
++++++++++++++

PostgreSQL's partitioning implementation in Django DB Parti is done purely at the database level. That means
that Django DB Parti creates several triggers and functions and inserts them directly into the database, so
even if you issue direct insert statement from database console and not from Django, everything will work as
expected and record will be inserted into the correct partition, if partition doesn't exist, it will be created
for you automatically. Also partitions may be created in any order and not only from lower to higher.

Partitioning types
++++++++++++++++++

* Range partitioning by date/datetime for the following periods:

  - day
  - week
  - month
  - year

Limitations
+++++++++++

* Currently there are no known limitations for this backend, except that not all partitioning types are supported.
  New types will be added in next releases of Django DB Parti.

MySQL
~~~~~

Implementation
++++++++++++++

MySQL's partitioning implementation in Django DB Parti is done in a mixed way, half at the python level and half
at the database level. Unfortunately MySQL doesn't support dynamic sql in triggers or functions that are called
within triggers, so the only way to create partitions automatically is to calculate everything at the python
level, then to create needed sql statements based on calculations and issue that statement into the database.

Partitioning types
++++++++++++++++++

* Range partitioning by date/datetime for the following periods:

  - day
  - week
  - month
  - year

Limitations
+++++++++++

* Not all partitioning types are supported. New types will be added in next releases of Django DB Parti.
* Partitioning is not available for bulk inserts (i.e. Django's bulk_create() method) because it doesn't call
  model's save() method which this backend relies on. Currently there is no known way to remove this limitation.
* New partitions can be created only from lower to higher, you can overcome this with MySQL's special command
  REORGANIZE PARTITION which you have to issue from the database console. You can read more about it at the
  MySQL's documentation. We plan to remove this limitation in one of the future releases of Django DB Parti.

Requirements
------------

* Django_ 1.5.x (may work with older versions, but untested)

Installation
------------

From pypi_:

.. code-block:: bash

    $ pip install django-db-parti

or clone from github_:

.. code-block:: bash

    $ git clone git://github.com/maxtepkeev/django-db-parti.git

Configuration
-------------

Add dbparti to PYTHONPATH and installed applications:

.. code-block:: python

    INSTALLED_APPS = (
        ...
        'dbparti'
    )

Create the model as usual which will represent the partitioned table and run syncdb to create a table for the
model, if you are using South for migrations, you can also create the model as usual via migrate. No additional
steps required. After that we need to make a few changes to the model:

| 1) In models.py add the following import statement at the top of the file:

.. code-block:: python

    from dbparti.models import Partitionable

| 2) Make your model to inherit from Partitionable, to do that change:

.. code-block:: python

    class YourModelName(models.Model):

to:

.. code-block:: python

    class YourModelName(Partitionable):

| 3) Add a Meta class to your model which inherits from Partitionable.Meta with a few settings (or if you already
     have a Meta class change it as the following, keep in mind that this is just an example configuration for a
     model, you have to enter values which represent your exact situation):

.. code-block:: python

    class Meta(Partitionable.Meta):
        partition_type = 'range'
        partition_subtype = 'date'
        partition_range = 'month'
        partition_column = 'added'

| 4) Lastly we need to initialize some database stuff, to do that execute the following command:

.. code-block:: bash

    $ python manage.py partition app_name

That's it! Easy right?! Now a few words about what we just did. We made our model to inherit from Partitionable,
also we used "month" as partition range and "added" as partition column, that means that from now on, a new
partition will be created every month and a value from "added" column will be used to determine into what
partition the data should be saved. Keep in mind that if you add new partitioned models to your apps or change
any settings in the existing partitioned models, you need to rerun the command from step 4, otherwise the database
won't know about your changes. You can also customize how data from that model will be displayed in the Django
admin interface, for that you need to do the following:

| 1) In admin.py add the following import statement at the top of the file:

.. code-block:: python

    from dbparti.admin import PartitionableAdmin

| 2) Create admin model as usual and then change:

.. code-block:: python

    class YourAdminModelName(admin.ModelAdmin):

to:

.. code-block:: python

    class YourAdminModelName(PartitionableAdmin):

| 3) Add a setting inside ModelAdmin class which tells how records are displayed in Django admin interface:

.. code-block:: python

    partition_show = 'all'

Available settings
------------------

Model settings
~~~~~~~~~~~~~~

All model settings are done inside model's Meta class which should inherit from Partitionable.Meta

``partition_type`` - what partition type will be used on the model, currently accepts the following:

* range

``partition_subtype`` - what partition subtype will be used on the model, currently used only when
"partition_type" is set to "range" and accepts the following values:

* date

``partition_range`` - how often a new partition will be created, currently accepts the following:

* day
* week
* month
* year

``partition_column`` - column, which value will be used to determine which partition record belongs to

ModelAdmin settings
~~~~~~~~~~~~~~~~~~~

All model admin settings are done inside model admin class itself

``partition_show`` - data from which partition will be shown in Django admin, accepts the following values:

* all (default)
* current
* previous

Example
-------

Let's imagine that we would like to create a table for storing log files. Without partitioning our table would
have millions of rows very soon and as the table grows performance will become slower. With partitioning we can
tell database that we want a new table to be created every month and that we will use a value from some column
to determine to which partition every new record belongs to. To be more specific let's call our table "logs", it
will have only 3 columns: id, content and added. Now when we insert the following record: id='1', content='blah',
added='2013-05-20', this record will be inserted not to our "logs" table but to the "logs_y2013m05" partition,
then if we insert another record like that: id='2', content='yada', added='2013-07-16' it will be inserted to the
partition "logs_y2013m07" BUT the great thing about all of that is that you are doing your inserts/updates/selects
on the table "logs"! Again, you are working with the table "logs" as usual and you don't may even know that
actually your data is stored in a lot of different partitions, everything is done for you automatically at the
database level, isn't that cool ?!

Contact and Support
-------------------

I will be glad to get your feedback, pull requests, issues, whatever. Feel free to contact me for any questions.

Copyright and License
---------------------

``django-db-parti`` is protected by BSD licence. Check the LICENCE_ for details.

.. _LICENCE: https://github.com/maxtepkeev/django-db-parti/blob/master/LICENSE
.. _pypi: https://pypi.python.org/pypi/django-db-parti
.. _github: https://github.com/maxtepkeev/django-db-parti
.. _Django: https://www.djangoproject.com
