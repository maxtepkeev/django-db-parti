from dbparti.models import Partitionable
from django.db.models import get_models
from django.core.management.base import AppCommand


class Command(AppCommand):
    help = 'Configures the database for partitioned models'

    def handle_app(self, app, **options):
        """Configures all needed database stuff depending on the backend used"""
        names = []

        for model in get_models(app):
            if issubclass(model, Partitionable):
                names.append(model.__name__)

                model_instance = model()
                model_instance.get_partition().prepare()

        if not names:
            self.stderr.write('Unable to find any partitionable models in an app: ' + app.__name__.split('.')[0] + '\n')
        else:
            self.stdout.write(
                'Successfully (re)configured the database for the following models: ' + ', '.join(names) + '\n'
            )
