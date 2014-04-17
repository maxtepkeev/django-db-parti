from dbparti.backends import BasePartition, transaction
from dbparti.backends.exceptions import (
    PartitionRangeError,
    PartitionRangeSubtypeError
)


"""
PostgreSQL partition backend.

PostgreSQL supports partitioning via inheritance.
"""
class Partition(BasePartition):
    """Common methods for all partition types"""
    def prepare(self):
        """Prepares needed triggers and functions for those triggers"""
        self.cursor.execute("""
            -- We need to create a before insert function
            CREATE OR REPLACE FUNCTION {parent_table}_insert_child()
            RETURNS TRIGGER AS $$
                {partition_function}
            $$ LANGUAGE plpgsql;

            -- Then we create a trigger which calls the before insert function
            DO $$
            BEGIN
            IF NOT EXISTS(
                SELECT 1
                FROM information_schema.triggers
                WHERE event_object_table = '{parent_table}'
                AND trigger_name = 'before_insert_{parent_table}_trigger'
            ) THEN
                CREATE TRIGGER before_insert_{parent_table}_trigger
                    BEFORE INSERT ON {parent_table}
                    FOR EACH ROW EXECUTE PROCEDURE {parent_table}_insert_child();
            END IF;
            END $$;

            -- Then we create a function to delete duplicate row from the master table after insert
            CREATE OR REPLACE FUNCTION {parent_table}_delete_master()
            RETURNS TRIGGER AS $$
                BEGIN
                    DELETE FROM ONLY {parent_table} WHERE {pk} = NEW.{pk};
                    RETURN NEW;
                END;
            $$ LANGUAGE plpgsql;

            -- Lastly we create the after insert trigger that calls the after insert function
            DO $$
            BEGIN
            IF NOT EXISTS(
                SELECT 1
                FROM information_schema.triggers
                WHERE event_object_table = '{parent_table}'
                AND trigger_name = 'after_insert_{parent_table}_trigger'
            ) THEN
                CREATE TRIGGER after_insert_{parent_table}_trigger
                    AFTER INSERT ON {parent_table}
                    FOR EACH ROW EXECUTE PROCEDURE {parent_table}_delete_master();
            END IF;
            END $$;
        """.format(
            pk=self.partition_pk.column,
            parent_table=self.table,
            partition_function=self._get_partition_function()
        ))

        transaction.commit_unless_managed()

    def exists(self):
        """Checks if partition exists. Not used in this backend because everything is done at the database level"""
        return True

    def create(self):
        """Creates new partition. Not used in this backend because everything is done at the database level"""
        pass


class RangePartition(Partition):
    """Range partition type implementation"""
    def __init__(self, *args, **kwargs):
        super(RangePartition, self).__init__(*args, **kwargs)
        self.partition_range = kwargs['partition_range']
        self.partition_subtype = kwargs['partition_subtype']

    def _get_partition_function(self):
        """Dynamically loads needed before insert function body depending on the partition subtype"""
        try:
            return getattr(self, '_get_{0}_partition_function'.format(self.partition_subtype))()
        except AttributeError:
            import re
            raise PartitionRangeSubtypeError(
                model=self.model,
                current_value=self.partition_subtype,
                allowed_values=[re.match('_get_(\w+)_partition_function', c).group(1) for c in dir(
                    self) if re.match('_get_\w+_partition_function', c) is not None]
            )

    def _get_date_partition_function(self):
        """Contains a before insert function body for date partition subtype"""
        patterns = {
            'day': '"y"YYYY"d"DDD',
            'week': '"y"IYYY"w"IW',
            'month': '"y"YYYY"m"MM',
            'year': '"y"YYYY',
        }

        try:
            partition_pattern = patterns[self.partition_range]
        except KeyError:
            raise PartitionRangeError(model=self.model, current_value=self.partition_range, allowed_values=patterns.keys())

        return """
            DECLARE tablename TEXT;
            DECLARE columntype TEXT;
            DECLARE startdate TIMESTAMP;
            BEGIN
                startdate := date_trunc('{partition_range}', NEW.{partition_column});
                tablename := '{parent_table}_' || to_char(NEW.{partition_column}, '{partition_pattern}');

                IF NOT EXISTS(
                    SELECT 1 FROM information_schema.tables WHERE table_name=tablename)
                THEN
                    SELECT data_type INTO columntype
                    FROM information_schema.columns
                    WHERE table_name = '{parent_table}' AND column_name = '{partition_column}';

                    EXECUTE 'CREATE TABLE ' || tablename || ' (
                        CHECK (
                            {partition_column} >= ''' || startdate || '''::' || columntype || ' AND
                            {partition_column} < ''' || (startdate + '1 {partition_range}'::interval) || '''::' || columntype || '
                        )
                    ) INHERITS ({parent_table});';

                    EXECUTE 'CREATE INDEX ' || tablename || '_{partition_column} ON ' || tablename || ' ({partition_column});';
                END IF;

                EXECUTE 'INSERT INTO ' || tablename || ' VALUES (($1).*);' USING NEW;
                RETURN NEW;
            END;
        """.format(
            parent_table=self.table,
            partition_range=self.partition_range,
            partition_column=self.partition_column,
            partition_pattern=partition_pattern
        )
