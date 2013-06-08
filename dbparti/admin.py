from django.contrib import admin
from dbparti.utilities import DateTimeMixin


class PartitionableAdmin(DateTimeMixin, admin.ModelAdmin):
    partition_show = 'all'

    def __init__(self, *args, **kwargs):
        """Initializes all the parent classes"""
        admin.ModelAdmin.__init__(self, *args, **kwargs)
        DateTimeMixin.__init__(
            self,
            self.partition_show,
            self.opts.partition_range,
            None,
            self.opts.get_field(self.opts.partition_column).get_internal_type(),
        )

    def queryset(self, request):
        """Determines data from what partitions should be shown in django admin"""
        fday, lday = self.get_partition_show_period(self.get_datetime_string('date'))
        qs = super(PartitionableAdmin, self).queryset(request)

        if fday is None and lday is None:
            qs = qs.all()
        else:
            qs = qs.filter(
                **{self.opts.partition_column + '__gte': fday, self.opts.partition_column + '__lte': lday}
            )

        return qs
