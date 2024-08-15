-- create_schema.sql

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
