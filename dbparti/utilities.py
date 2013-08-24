from datetime import datetime, timedelta


class DateTimeMixin(object):
    PARTITION_SHOWS = ('all', 'current', 'previous')
    PARTITION_RANGES = ('month', 'week')
    PARTITION_COLUMN_TYPES = {
        'DateField': {'type': 'date', 'workdate': datetime.now().date()},
        'DateTimeField': {'type': 'time', 'workdate': datetime.now()}
    }

    def __init__(self, **kwargs):
        """Initializes all the datetime logic needed for datetime partitioning"""
        self.partition_show = kwargs.get('partition_show', self.PARTITION_SHOWS[0])
        self.partition_range = kwargs.get('partition_range', self.PARTITION_RANGES[0])

        partition_column_val = kwargs.get('partition_column_val', None)
        partition_column_type = kwargs.get('partition_column_type', 'Unknown')

        if self.partition_show not in self.PARTITION_SHOWS:
            raise Exception('Unknown partition show type "{0}", allowed types are: {1}'.format(
                self.partition_show, ', '.join(self.PARTITION_SHOWS)))
        if self.partition_range not in self.PARTITION_RANGES:
            raise Exception('Unknown partition range type "{0}", allowed types are: {1}'.format(
                self.partition_range, ', '.join(self.PARTITION_RANGES)))

        try:
            self.datetype = self.PARTITION_COLUMN_TYPES[partition_column_type]['type']
            self.workdate = partition_column_val if partition_column_val is not None else \
                self.PARTITION_COLUMN_TYPES[partition_column_type]['workdate']
        except KeyError:
            raise Exception('Unknown partition column type "{0}", allowed types are: {1}'.format(
                partition_column_type, ', '.join(list(self.PARTITION_COLUMN_TYPES.keys()))))

    def get_datetype(self):
        """Returns the current datetype (date or time)"""
        return self.datetype

    def get_datetime_string(self, dttype):
        """Returns datetime string compatible with strftime depending on datetype"""
        return '%Y-%m-%d' if dttype == 'date' else '%Y-%m-%d %H:%M:%S.%f'

    def get_partition_name(self):
        """Returns partition name depending on the current workdate"""
        return '_' + self.workdate.strftime(getattr(self, 'partition_name_for_' + self.partition_range)())

    def get_partition_range_period(self, timestring):
        """Returns partition period start and end depending on the current workdate and datetype"""
        return getattr(self, 'partition_period_for_' + self.partition_range)(self.workdate, timestring)

    def get_partition_show_period(self, timestring):
        """Returns partition period start and end for the django admin"""
        if self.partition_show == 'all':
            return None, None
        elif self.partition_show == 'previous':
            if self.partition_range == 'week':
                dt = datetime.now().date() - timedelta(weeks=1)
            elif self.partition_range == 'month':
                today = datetime.now().date()
                dt = datetime(today.year, today.month, 1) - timedelta(days=1)
        elif self.partition_show == 'current':
            dt = datetime.now().date()

        return getattr(self, 'partition_period_for_' + self.partition_range)(dt, timestring)

    @classmethod
    def partition_name_for_week(cls):
        """Returns strftime compatible partition name part for week partition range"""
        return 'y%Yw%V'

    @classmethod
    def partition_name_for_month(cls):
        """Returns strftime compatible partition name part for month partition range"""
        return 'y%Ym%m'

    @classmethod
    def partition_period_for_week(cls, today, timestring):
        """Returns partition period start and end for week partition range"""
        dt = datetime(today.year, 1, 1)

        if dt.weekday() > 3:
            dt = dt + timedelta(7 - dt.weekday())
        else:
            dt = dt - timedelta(dt.weekday())

        dlt = timedelta(days=(int(today.strftime('%V')) - 1) * 7)
        fday = (dt + dlt).strftime(timestring)
        lday = (dt + dlt + timedelta(days=6)).strftime(timestring)

        return fday, lday

    @classmethod
    def partition_period_for_month(cls, today, timestring):
        """Returns partition period start and end for month partition range"""
        fday = datetime(today.year, today.month, 1).strftime(timestring)
        lday = (datetime(today.year, today.month + 1, 1) - timedelta(days=1)).strftime(timestring)
        return fday, lday
