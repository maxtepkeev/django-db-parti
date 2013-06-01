from django.db import connection, transaction


class Postgresql(object):
    def __init__(self, table, partition_column):
        self.table = table
        self.cursor = connection.cursor()
        self.partition_column = partition_column

    def partition_exists(self, partition_name):
        self.cursor.execute('SELECT EXISTS(SELECT 1 FROM information_schema.tables WHERE table_name=%s)',
            (self.table + partition_name,))
        return self.cursor.fetchone()[0]

    def create_partition(self, partition_name, datetype, fday, lday):
        self.cursor.execute('''
            -- We need to create a table first
            CREATE TABLE {child_table} (
                CHECK ( {partition_column} >= {datetype} '{fday}' AND {partition_column} <= {datetype} '{lday}' )
            ) INHERITS ({parent_table});

            -- Then we create an index to speed up things a little
            CREATE INDEX {child_table}_{partition_column} ON {child_table} ({partition_column});

            -- Now we need to create a before insert function
            CREATE OR REPLACE FUNCTION {parent_table}_insert_child()
            RETURNS TRIGGER AS $$
                BEGIN
                    INSERT INTO {child_table} VALUES (NEW.*);
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
            child_table=self.table + partition_name,
            parent_table=self.table,
            partition_column=self.partition_column,
            fday=fday,
            lday=lday,
            datetype='DATE' if datetype == 'date' else 'TIMESTAMP',
        ))

        transaction.commit_unless_managed()
