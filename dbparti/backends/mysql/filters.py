from dbparti.backends import BasePartitionFilter
from dbparti.backends.exceptions import (
    PartitionRangeError,
    PartitionRangeSubtypeError,
    PartitionShowError
)


"""MySQL backend partition filters for django admin"""
class PartitionFilter(BasePartitionFilter):
    """Common methods for all partition filters"""
    pass


class RangePartitionFilter(PartitionFilter):
    """Range partition filter implementation"""
    def __init__(self, *args, **kwargs):
        super(RangePartitionFilter, self).__init__(*args, **kwargs)
        self.partition_range = kwargs['partition_range']
        self.partition_subtype = kwargs['partition_subtype']

    def apply(self):
        """Dynamically loads needed partition filter depending on the partition subtype"""
        try:
            return getattr(self, '_get_{0}_filter'.format(self.partition_subtype))()
        except AttributeError:
            import re
            raise PartitionRangeSubtypeError(
                model=self.model,
                current_value=self.partition_subtype,
                allowed_values=[re.match('_get_(\w+)_filter', c).group(1) for c in dir(
                    self) if re.match('_get_\w+_filter', c) is not None]
            )

    def _get_date_filter(self):
        """Contains a partition filter for date partition subtype"""
        ranges = {
            'year': [
                "EXTRACT(YEAR FROM {0}.{1}) = EXTRACT(YEAR FROM {2})",
            ],
            'month': [
                "EXTRACT(YEAR FROM {0}.{1}) = EXTRACT(YEAR FROM NOW())",
                "EXTRACT(MONTH FROM {2}.{3}) = EXTRACT(MONTH FROM {4})",
            ],
            'week': [
                "EXTRACT(YEAR FROM {0}.{1}) = EXTRACT(YEAR FROM NOW())",
                "EXTRACT(WEEK FROM {2}.{3}) = EXTRACT(WEEK FROM {4})",
            ],
            'day': [
                "EXTRACT(YEAR FROM {0}.{1}) = EXTRACT(YEAR FROM NOW())",
                "EXTRACT(MONTH FROM {2}.{3}) = EXTRACT(MONTH FROM NOW())",
                "EXTRACT(DAY FROM {4}.{5}) = EXTRACT(DAY FROM {6})",
            ],
        }

        try:
            show_range = ranges[self.partition_range]
        except KeyError:
            raise PartitionRangeError(model=self.model, current_value=self.partition_range, allowed_values=ranges.keys())

        shows = {
            'current': 'NOW()',
            'previous': 'NOW() - INTERVAL 1 {0}',
        }

        try:
            show = shows[self.partition_show]
        except KeyError:
            raise PartitionShowError(model=self.model, current_value=self.partition_show, allowed_values=shows.keys())

        return [item.format(self.table, self.partition_column, show.format(self.partition_range)) for item in show_range]
