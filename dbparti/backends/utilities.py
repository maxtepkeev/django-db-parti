from datetime import datetime, timedelta
from dbparti.backends.exceptions import PartitionRangeError


"""Provides date and time calculations for some database backends"""
class DateTimeUtil(object):
    def __init__(self, now, period, format='%Y-%m-%d %H:%M:%S', model=None):
        self.now = now
        self.period = period
        self.format = format
        self.model = model

    def get_name(self):
        """Returns name of the partition depending on the given date and period"""
        patterns = {
            'day': {'real': 'y%Yd%j', 'none': 'y0000d000'},
            'week': {'real': 'y%Yw%V', 'none': 'y0000w00'},
            'month': {'real': 'y%Ym%m', 'none': 'y0000m00'},
            'year': {'real': 'y%Y', 'none': 'y0000'},
        }

        try:
            return patterns[self.period]['none'] if self.now is None else self.now.strftime(patterns[self.period]['real'])
        except KeyError:
            raise PartitionRangeError(model=self.model, current_value=self.period, allowed_values=patterns.keys())

    def get_period(self):
        """Dynamically returns beginning and an end depending on the given period"""
        try:
            return getattr(self, '_get_{0}_period'.format(self.period))()
        except AttributeError:
            import re
            raise PartitionRangeError(
                model=self.model,
                current_value=self.period,
                allowed_values=[re.match('_get_(\w+)_period', c).group(1) for c in dir(
                    self) if re.match('_get_\w+_period', c) is not None]
            )

    def _get_day_period(self):
        """Returns beginning and an end for a day period"""
        start = self.now.replace(hour=0, minute=0, second=0, microsecond=0)
        end = self.now.replace(hour=23, minute=59, second=59, microsecond=999999)

        return start.strftime(self.format), end.strftime(self.format)

    def _get_week_period(self):
        """Returns beginning and an end for a week period"""
        date_ = datetime(self.now.year, 1, 1)

        if date_.weekday() > 3:
            date_ = date_ + timedelta(7 - date_.weekday())
        else:
            date_ = date_ - timedelta(date_.weekday())

        days = timedelta(days=(int(self.now.strftime('%V')) - 1) * 7)

        start = (date_ + days)
        end = (date_ + days + timedelta(days=6)).replace(hour=23, minute=59, second=59, microsecond=999999)

        return start.strftime(self.format), end.strftime(self.format)

    def _get_month_period(self):
        """Returns beginning and an end for a month period"""
        fday = datetime(self.now.year, self.now.month, 1)

        if self.now.month == 12:
            lday = datetime(self.now.year, self.now.month, 31, 23, 59, 59, 999999)
        else:
            lday = (datetime(self.now.year, self.now.month + 1, 1, 23, 59, 59, 999999) - timedelta(days=1))

        return fday.strftime(self.format), lday.strftime(self.format)

    def _get_year_period(self):
        """Returns beginning and an end for a year period"""
        fday = datetime(self.now.year, 1, 1)
        lday = (datetime(self.now.year + 1, 1, 1, 23, 59, 59, 999999) - timedelta(days=1))

        return fday.strftime(self.format), lday.strftime(self.format)
