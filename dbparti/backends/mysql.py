from django.db import connection, transaction

"""
MySQL backend for Django DB Parti.

Thing to keep in mind is that MySQLdb doesn't support compound MySQL statements,
so each separate statement should be executed inside each self.cursor.execute().
Also MySQL has a lot of limitations for partitioned tables, please see MySQL site.
"""
class Mysql(object):
    def __init__(self, table, partition_column, datetype):
        self.table = table
        self.cursor = connection.cursor()
        self.partition_column = partition_column
        self.datetype = datetype

    def partition_exists(self, partition_name):
        """Checks whether partition exists"""
        self.cursor.execute('''
            SELECT EXISTS(
                SELECT 1 FROM information_schema.partitions
                WHERE table_name='{parent_table}' AND partition_name='{child_table}');
        '''.format(
            parent_table=self.table,
            child_table=partition_name.replace('_', ''),
        ))
        return self.cursor.fetchone()[0]

    def create_partition(self, partition_name, fday, lday):
        """Creates partition with the given parameters"""
        self.cursor.execute('''
            ALTER TABLE {parent_table} ADD PARTITION (
                PARTITION {child_table} VALUES LESS THAN ({datetype}('{lday}') + {addition})
            );
        '''.format(
            child_table=partition_name.replace('_', ''),
            parent_table=self.table,
            lday=lday,
            addition='1' if self.datetype == 'date' else '86400',
            datetype='TO_DAYS' if self.datetype == 'date' else 'UNIX_TIMESTAMP',
        ))

        transaction.commit_unless_managed()

    def init_partition(self, partition_range):
        """Initializes needed database stuff"""
        self.cursor.execute('''
            -- We need to rebuild primary key for our partitioning to work
            ALTER table {parent_table} DROP PRIMARY KEY, add PRIMARY KEY (`id`,`{partition_column}`);
        '''.format(
            parent_table=self.table,
            partition_column=self.partition_column,
        ))

        self.cursor.execute('''
            -- Then we create zero partition to speed up things due to the partitioning
            -- implementation in the early versions of MySQL database (see bug #49754)
            ALTER TABLE {parent_table} PARTITION BY RANGE ({datetype}({partition_column}))(
                PARTITION {partition_pattern} VALUES LESS THAN (0)
            );
        '''.format(
            parent_table=self.table,
            partition_column=self.partition_column,
            partition_pattern=self.pattern_for_partition_range(partition_range),
            datetype='TO_DAYS' if self.datetype == 'date' else 'UNIX_TIMESTAMP',
        ))

        transaction.commit_unless_managed()

    @classmethod
    def pattern_for_partition_range(cls, partition_range):
        """Returns datetime pattern depending on the given partition range"""
        patterns = {
            'week': 'y0000w00',
            'month': 'y0000m00',
        }

        return patterns[partition_range]
