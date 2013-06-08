from django.db import connection, transaction


class Postgresql(object):
    def __init__(self, table, partition_column):
        self.table = table
        self.cursor = connection.cursor()
        self.partition_column = partition_column

    def partition_exists(self, partition_name):
        """Checks whether partition exists"""
        self.cursor.execute('SELECT EXISTS(SELECT 1 FROM information_schema.tables WHERE table_name=%s)',
            (self.table + partition_name,))
        return self.cursor.fetchone()[0]

    def create_partition(self, partition_name, datetype, fday, lday):
        """Creates partition with the given parameters"""
        self.cursor.execute('''
            -- We need to create a table first
            CREATE TABLE {child_table} (
                CHECK ({partition_column} >= {datetype} '{fday}' AND {partition_column} <= {datetype} '{lday}')
            ) INHERITS ({parent_table});

            -- Then we create an index to speed up things a little
            CREATE INDEX {child_table}_{partition_column} ON {child_table} ({partition_column});
        '''.format(
            child_table=self.table + partition_name,
            parent_table=self.table,
            partition_column=self.partition_column,
            fday=fday,
            lday=lday,
            datetype='DATE' if datetype == 'date' else 'TIMESTAMP',
        ))

        transaction.commit_unless_managed()

    def init_partition(self, partition_range):
        """Initializes needed triggers and functions for those triggers"""
        self.cursor.execute('''
            -- We need to create a before insert function
            CREATE OR REPLACE FUNCTION {parent_table}_insert_child()
            RETURNS TRIGGER AS $$
                DECLARE tablename TEXT;
                BEGIN
                    tablename := '{parent_table}_' || to_char(NEW.{partition_column}, '{partition_pattern}');
                    EXECUTE 'INSERT INTO ' || tablename || ' VALUES (($1).*);' USING NEW;
                    RETURN NEW;
                END;
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
                    DELETE FROM ONLY {parent_table} WHERE id = NEW.id;
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
        '''.format(
            parent_table=self.table,
            partition_column=self.partition_column,
            partition_pattern=self.pattern_for_partition_range(partition_range),
        ))

        transaction.commit_unless_managed()

    @classmethod
    def pattern_for_partition_range(cls, partition_range):
        """Returns datetime pattern depending on the given partition range"""
        patterns = {
            'week': '"y"IYYY"w"IW',
            'month': '"y"YYYY"m"MM',
        }

        return patterns[partition_range]
