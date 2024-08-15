from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):
    help = 'Создать схемы rpt и dcm'

    def handle(self, *args, **kwargs):
        with connection.cursor() as cursor:
            cursor.execute("""
            DO $$
            BEGIN
              IF NOT EXISTS (SELECT 1 FROM information_schema.schemata WHERE schema_name = 'rpt') THEN
                CREATE SCHEMA rpt;
              END IF;

              IF NOT EXISTS (SELECT 1 FROM information_schema.schemata WHERE schema_name = 'dcm') THEN
                CREATE SCHEMA dcm;
              END IF;
              
              IF NOT EXISTS (SELECT 1 FROM information_schema.schemata WHERE schema_name = 'dct') THEN
                CREATE SCHEMA dct;
              END IF;
            END $$;
            """)
            self.stdout.write(self.style.SUCCESS('Схемы успешно созданы!'))
