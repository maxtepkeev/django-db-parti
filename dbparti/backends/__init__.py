from dbparti import connection, transaction


class BasePartition(object):
    """Base partition class for all backends. All backends should inherit from it."""
    def __init__(self, column_value, column_type, **kwargs):
        self.cursor = connection.cursor()
        self.model = kwargs['object_name']
        self.table = kwargs['db_table']
        self.partition_pk = kwargs['pk']
        self.partition_column = kwargs['partition_column']
        self.column_value = column_value
        self.column_type = column_type

    def prepare(self):
        """Prepares everything that is needed to initialize partitioning"""
        raise NotImplementedError('Prepare method not implemented for partition type: {0}'.format(self.__class__.__name__))

    def exists(self):
        """Checks if partition exists"""
        raise NotImplementedError('Exists method not implemented for partition type: {0}'.format(self.__class__.__name__))

    def create(self):
        """Creates new partition"""
        raise NotImplementedError('Create method not implemented for partition type: {0}'.format(self.__class__.__name__))

    def _get_name(self):
        """Defines name for a new partition"""
        raise NotImplementedError('Name method not implemented for partition type: {0}'.format(self.__class__.__name__))

    def _get_partition_function(self):
        """Contains a partition function that is used to create new partitions at database level"""
        raise NotImplementedError('Partition function method not implemented for partition type: {0}'.format(self.__class__.__name__))


class BasePartitionFilter(object):
    """Base class for all filter types. All filter types should inherit from it."""
    def __init__(self, partition_show, **kwargs):
        self.partition_show = partition_show
        self.model = kwargs['object_name']
        self.table = kwargs['db_table']
        self.partition_column = kwargs['partition_column']

    def apply(self):
        """Contains a filter that needs to be applied to queryset"""
        raise NotImplementedError('Filter not implemented for type: {0}'.format(self.__class__.__name__))
