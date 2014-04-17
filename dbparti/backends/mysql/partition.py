from dbparti.backends import BasePartition, transaction
from dbparti.backends.utilities import DateTimeUtil
from dbparti.backends.exceptions import PartitionRangeSubtypeError, PartitionFunctionError


"""
MySQL partition backend.

MySQL supports partitioning natively via PARTITION BY clause. Thing to keep in
mind is that python MySQLdb doesn't support compound MySQL statements, so each
separate statement should be executed inside each self.cursor.execute().
"""
class Partition(BasePartition):
    """Common methods for all partition types"""
    def prepare(self):
        """Converts original table to partitioned one"""
        self.cursor.execute("""
            -- We need to rebuild primary key for our partitioning to work
            ALTER table {parent_table} DROP PRIMARY KEY, add PRIMARY KEY ({pk}, {partition_column});
        """.format(
            pk=self.partition_pk.column,
            parent_table=self.table,
            partition_column=self.partition_column,
        ))

        transaction.commit_unless_managed()

    def exists(self):
        """Checks if partition exists"""
        self.cursor.execute("""
            SELECT EXISTS(
                SELECT 1 FROM information_schema.partitions
                WHERE table_name='{parent_table}' AND partition_name='{partition_name}');
        """.format(
            parent_table=self.table,
            partition_name=self._get_name(),
        ))

        return self.cursor.fetchone()[0]


class RangePartition(Partition):
    """Range partition type implementation"""
    def __init__(self, *args, **kwargs):
        super(RangePartition, self).__init__(*args, **kwargs)
        self.partition_range = kwargs['partition_range']
        self.partition_subtype = kwargs['partition_subtype']
        self.datetime = DateTimeUtil(self.column_value, self.partition_range, model=self.model)

    def prepare(self):
        """Converts original table to partitioned one"""
        super(RangePartition, self).prepare()
        self.datetime.now = None

        self.cursor.execute("""
            -- We need to create zero partition to speed up things due to the partitioning
            -- implementation in the early versions of MySQL database (see bug #49754)
            ALTER TABLE {parent_table} PARTITION BY RANGE ({function}({partition_column}))(
                PARTITION {partition_pattern} VALUES LESS THAN (0)
            );
        """.format(
            parent_table=self.table,
            partition_column=self.partition_column,
            partition_pattern=self._get_name(),
            function=self._get_partition_function(),
        ))

        transaction.commit_unless_managed()

    def create(self):
        """Creates new partition"""
        self.cursor.execute("""
            ALTER TABLE {parent_table} ADD PARTITION (
                PARTITION {child_table} VALUES LESS THAN ({function}('{period_end}') + {addition})
            );
        """.format(
            child_table=self._get_name(),
            parent_table=self.table,
            function=self._get_partition_function(),
            period_end=self.datetime.get_period()[1],
            addition='86400' if self._get_column_type() == 'timestamp' else '1',
        ))

        transaction.commit_unless_managed()

    def _get_name(self):
        """Dynamically defines new partition name depending on the partition subtype"""
        try:
            return getattr(self, '_get_{0}_name'.format(self.partition_subtype))()
        except AttributeError:
            import re
            raise PartitionRangeSubtypeError(
                model=self.model,
                current_value=self.partition_subtype,
                allowed_values=[re.match('_get_(\w+)_name', c).group(1) for c in dir(
                    self) if re.match('_get_\w+_name', c) is not None]
            )

    def _get_date_name(self):
        """Defines name for a new partition for date partition subtype"""
        return '{0}_{1}'.format(self.table, self.datetime.get_name())

    def _get_partition_function(self):
        """Returns correct partition function depending on the MySQL column type"""
        functions = {
            'date': 'TO_DAYS',
            'datetime': 'TO_DAYS',
            'timestamp': 'UNIX_TIMESTAMP',
        }

        column_type = self._get_column_type()

        try:
            return functions[column_type]
        except KeyError:
            raise PartitionFunctionError(current_value=column_type, allowed_values=functions.keys())

    def _get_column_type(self):
        """
        We can't rely on self.column_type in MySQL, because Django uses only date
        and datetime types internally, but MySQL has an additional timestamp type
        and we need to know that, otherwise we can apply incorrect partition function
        """
        self.cursor.execute("""
            SELECT data_type
            FROM information_schema.columns
            WHERE table_name = '{parent_table}' AND column_name = '{partition_column}';
        """.format(
            parent_table=self.table,
            partition_column=self.partition_column,
        ))

        return self.cursor.fetchone()[0]
