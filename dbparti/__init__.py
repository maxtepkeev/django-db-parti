from django.db import connection, transaction
from dbparti.backends.exceptions import BackendError


try:
    backend = __import__('dbparti.backends.{0}'.format(connection.vendor), fromlist='*')
except ImportError:
    import pkgutil, os
    raise BackendError(
        allowed_values=[name for _, name, is_package in pkgutil.iter_modules(
            [os.path.join(os.path.dirname(__file__), 'backends')]) if is_package]
    )
