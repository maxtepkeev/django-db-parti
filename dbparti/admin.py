from django.contrib import admin
from dbparti import backend
from dbparti.backends.exceptions import PartitionColumnError, PartitionFilterError


class PartitionableAdmin(admin.ModelAdmin):
    partition_show = 'all'

    def __init__(self, *args, **kwargs):
        super(PartitionableAdmin, self).__init__(*args, **kwargs)

        if not self.opts.partition_column in self.opts.get_all_field_names():
            raise PartitionColumnError(
                model=self.opts.__dict__['object_name'],
                current_value=self.opts.partition_column,
                allowed_values=self.opts.get_all_field_names()
            )

        try:
            self.filter = getattr(backend.filters, '{0}PartitionFilter'.format(
                self.opts.partition_type.capitalize()))(self.partition_show, **self.opts.__dict__)
        except AttributeError:
            import re
            raise PartitionFilterError(
                model=self.opts.__dict__['object_name'],
                current_value=self.opts.partition_type,
                allowed_values=[c.replace('PartitionFilter', '').lower() for c in dir(
                    backend.filters) if re.match('\w+PartitionFilter', c) is not None and 'Base' not in c]
            )

    def queryset(self, request):
        """Determines data from what partitions should be shown in django admin"""
        qs = super(PartitionableAdmin, self).queryset(request)

        if self.partition_show != 'all':
            qs = qs.extra(where=self.filter.apply())

        return qs
