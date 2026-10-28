from unittest.mock import patch

import psycopg
from django.db.backends.postgresql.creation import DatabaseCreation
from django.test.runner import DiscoverRunner


class SchemaTestRunner(DiscoverRunner):
    def setup_databases(self, **kwargs):
        original = DatabaseCreation._create_test_db

        def create_with_schemas(creation, verbosity, autoclobber, keepdb=False):
            name = creation._get_test_db_name()
            if not name.startswith('test_pfbase_security_'):
                raise RuntimeError('Security tests require an isolated test_pfbase_security_* database.')
            result = original(creation, verbosity, autoclobber, keepdb)
            params = creation.connection.get_connection_params()
            params['dbname'] = name
            with psycopg.connect(**params) as connection:
                with connection.cursor() as cursor:
                    for schema in ('stm', 'dct', 'dcm'):
                        cursor.execute(f'CREATE SCHEMA IF NOT EXISTS {schema}')
            return result

        with patch.object(DatabaseCreation, '_create_test_db', create_with_schemas):
            return super().setup_databases(**kwargs)
