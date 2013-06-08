from django.db import models, connection
from dbparti.utilities import DateTimeMixin


models.options.DEFAULT_NAMES += ('partition_range', 'partition_column')

class Partitionable(DateTimeMixin, models.Model):
    def __init__(self, *args, **kwargs):
        """Initializes all the parent classes and the current database backend"""
        models.Model.__init__(self, *args, **kwargs)
        DateTimeMixin.__init__(
            self,
            False,
            self._meta.partition_range,
            getattr(self, self._meta.partition_column),
            self._meta.get_field(self._meta.partition_column).get_internal_type(),
        )

        self.db = getattr(__import__('dbparti.backends.' + connection.vendor,
            fromlist=[connection.vendor.capitalize()]), connection.vendor.capitalize())(
                self._meta.db_table, self._meta.partition_column)

    def save(self, *args, **kwargs):
        """Determines into what partition the data should be saved"""
        fday, lday = self.get_partition_range_period(self.get_datetime_string('date'))

        if not self.db.partition_exists(self.get_partition_name()):
            self.db.create_partition(self.get_partition_name(), self.get_datetype(), fday, lday)

        super(Partitionable, self).save(*args, **kwargs)

    class Meta:
        abstract = True
        partition_range = 'month'
        partition_column = 'partdate'
