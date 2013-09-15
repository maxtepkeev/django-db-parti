from django.db import models
from dbparti import backend
from dbparti.backends.exceptions import PartitionColumnError, PartitionTypeError


models.options.DEFAULT_NAMES += (
    'partition_range',
    'partition_column',
    'partition_type',
    'partition_subtype',
    'partition_list',
)

class Partitionable(models.Model):
    def __init__(self, *args, **kwargs):
        super(Partitionable, self).__init__(*args, **kwargs)

        try:
            column_value = getattr(self, self._meta.partition_column)
            column_type = self._meta.get_field(self._meta.partition_column).get_internal_type()
        except AttributeError:
            raise PartitionColumnError(
                model=self.__class__.__name__,
                current_value=self._meta.partition_column,
                allowed_values=self._meta.get_all_field_names()
            )

        try:
            self.partition = getattr(backend.partition, '{}Partition'.format(
                self._meta.partition_type.capitalize()))(column_value, column_type, **self._meta.__dict__)
        except AttributeError:
            import re
            raise PartitionTypeError(
                model=self.__class__.__name__,
                current_value=self._meta.partition_type,
                allowed_values=[c.replace('Partition', '').lower() for c in dir(
                    backend.partition) if re.match('\w+Partition', c) is not None and 'Base' not in c]
            )

    def save(self, *args, **kwargs):
        if not self.partition.exists():
            self.partition.create()

        super(Partitionable, self).save(*args, **kwargs)

    class Meta:
        abstract = True
        partition_type = 'None'
        partition_subtype = 'None'
        partition_range = 'None'
        partition_column = 'None'
