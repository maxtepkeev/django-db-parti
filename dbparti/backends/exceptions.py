from dbparti import connection


class BasePartitionError(Exception):
    """Base exception class for backend exceptions"""
    def __init__(self, message, **kwargs):
        self.message = message
        self.model = kwargs.get('model', None)
        self.current_value = kwargs.get('current_value', None)
        self.allowed_values = kwargs.get('allowed_values', None)

    def __str__(self):
        return self.message.format(
            model=self.model,
            current=self.current_value,
            vendor=connection.vendor,
            allowed=', '.join(list(self.allowed_values))
        )


class BackendError(BasePartitionError):
    """Unsupported database backend"""
    def __init__(self, **kwargs):
        super(BackendError, self).__init__(
            'Unsupported database backend "{vendor}", supported backends are: {allowed}',
            **kwargs
        )


class PartitionColumnError(BasePartitionError):
    """Undefined partition column"""
    def __init__(self, **kwargs):
        super(PartitionColumnError, self).__init__(
            'Undefined partition column "{current}" in "{model}" model, available columns are: {allowed}',
            **kwargs
        )


class PartitionTypeError(BasePartitionError):
    """Unsupported partition type"""
    def __init__(self, **kwargs):
        super(PartitionTypeError, self).__init__(
            'Unsupported partition type "{current}" in "{model}" model, supported types for "{vendor}" backend are: {allowed}',
            **kwargs
        )


class PartitionFilterError(BasePartitionError):
    """Unsupported partition filter"""
    def __init__(self, **kwargs):
        super(PartitionFilterError, self).__init__(
            'Unsupported partition filter "{current}" in "{model}" model, supported filters for "{vendor}" backend are: {allowed}',
            **kwargs
        )


class PartitionRangeError(BasePartitionError):
    """Unsupported partition range"""
    def __init__(self, **kwargs):
        super(PartitionRangeError, self).__init__(
            'Unsupported partition range "{current}" in "{model}" model, supported partition ranges for backend "{vendor}" are: {allowed}',
            **kwargs
        )


class PartitionRangeSubtypeError(BasePartitionError):
    """Unsupported partition range subtype"""
    def __init__(self, **kwargs):
        super(PartitionRangeSubtypeError, self).__init__(
            'Unsupported partition range subtype "{current}" in "{model}" model, supported range subtypes for backend "{vendor}" are: {allowed}',
            **kwargs
        )


class PartitionShowError(BasePartitionError):
    """Unsupported partition show type"""
    def __init__(self, **kwargs):
        super(PartitionShowError, self).__init__(
            'Unsupported partition show type "{current}" in "{model}" admin class, supported partition show types for backend "{vendor}" are: {allowed}',
            **kwargs
        )


class PartitionFunctionError(BasePartitionError):
    """Unsupported partition function"""
    def __init__(self, **kwargs):
        super(PartitionFunctionError, self).__init__(
            'Unsupported partition function for column type "{current}", supported column types for "{vendor}" backend are: {allowed}',
            **kwargs
        )
