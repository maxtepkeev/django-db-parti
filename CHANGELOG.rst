.. :changelog:

Changelog
---------

0.1.5 (2013-06-08)
~~~~~~~~~~~~~~~~~~

- Updated readme
- Fixed postgresql backend error which sometimes tried to insert the data into partitions that don't exist
- Moved all the database partition system stuff to the command ``partition`` (see readme), that gave a lot
  in speed improvement becouse we don't need to check for trigger existance and some other things at runtime
  anymore

0.1.4 (2013-06-01)
~~~~~~~~~~~~~~~~~~

- Packaging fix

0.1.3 (2013-06-01)
~~~~~~~~~~~~~~~~~~

- Packaging fix

0.1.2 (2013-06-01)
~~~~~~~~~~~~~~~~~~

- Packaging fix

0.1.1 (2013-06-01)
~~~~~~~~~~~~~~~~~~

- Packaging fix

0.1.0 (2013-06-01)
~~~~~~~~~~~~~~~~~~

- Initial release
