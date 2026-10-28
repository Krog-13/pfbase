from django.db import migrations, models


AUDIT_SQL = """
CREATE FUNCTION stm.log_dcm_change() RETURNS trigger
LANGUAGE plpgsql SET search_path = pg_catalog AS $function$
DECLARE
    row_data jsonb;
    old_data jsonb;
    fields jsonb;
    action_name text;
BEGIN
    IF TG_OP = 'DELETE' THEN
        row_data := to_jsonb(OLD);
        fields := '[]'::jsonb;
        action_name := 'dcm_deleted';
    ELSE
        row_data := to_jsonb(NEW);
        IF TG_OP = 'INSERT' THEN
            SELECT COALESCE(jsonb_agg(key ORDER BY key), '[]'::jsonb)
              INTO fields FROM jsonb_each(row_data)
             WHERE key NOT IN ('id', 'created_at', 'updated_at');
            action_name := 'dcm_created';
        ELSE
            old_data := to_jsonb(OLD);
            SELECT COALESCE(jsonb_agg(key ORDER BY key), '[]'::jsonb)
              INTO fields FROM jsonb_each(row_data)
             WHERE key <> 'updated_at' AND old_data -> key IS DISTINCT FROM value;
            IF fields = '[]'::jsonb THEN
                RETURN NULL;
            END IF;
            action_name := 'dcm_updated';
            IF row_data -> 'is_deleted' IS DISTINCT FROM old_data -> 'is_deleted' THEN
                IF row_data ->> 'is_deleted' = 'true' THEN
                    action_name := 'dcm_soft_deleted';
                ELSIF row_data ->> 'is_deleted' = 'false' THEN
                    action_name := 'dcm_restored';
                END IF;
            END IF;
        END IF;
    END IF;

    INSERT INTO stm.security_event (
        created_at, actor_id, subject_id, event, result, reason, address, user_id,
        object_type, object_id, changed_fields, object_context
    ) VALUES (
        clock_timestamp(), NULLIF(current_setting('pfbase.actor_id', true), '')::bigint,
        NULL, action_name, 'success', '',
        NULLIF(current_setting('pfbase.actor_address', true), '')::inet, NULL,
        'dcm.' || TG_TABLE_NAME, (row_data ->> 'id')::bigint, fields,
        jsonb_strip_nulls(jsonb_build_object(
            'document_id', row_data -> 'document_id',
            'record_id', row_data -> 'record_id',
            'indicator_id', row_data -> 'indicator_id',
            'parent_id', row_data -> 'parent_id'
        ))
    );
    RETURN NULL;
END;
$function$;

CREATE TRIGGER dcm_change_audit AFTER INSERT OR UPDATE OR DELETE ON dcm.documents
    FOR EACH ROW EXECUTE FUNCTION stm.log_dcm_change();
CREATE TRIGGER dcm_change_audit AFTER INSERT OR UPDATE OR DELETE ON dcm.indicators
    FOR EACH ROW EXECUTE FUNCTION stm.log_dcm_change();
CREATE TRIGGER dcm_change_audit AFTER INSERT OR UPDATE OR DELETE ON dcm.records
    FOR EACH ROW EXECUTE FUNCTION stm.log_dcm_change();
CREATE TRIGGER dcm_change_audit AFTER INSERT OR UPDATE OR DELETE ON dcm.record_indicator_values
    FOR EACH ROW EXECUTE FUNCTION stm.log_dcm_change();
CREATE TRIGGER dcm_change_audit AFTER INSERT OR UPDATE OR DELETE ON dcm.record_history
    FOR EACH ROW EXECUTE FUNCTION stm.log_dcm_change();
"""

REVERSE_SQL = """
DROP TRIGGER dcm_change_audit ON dcm.record_history;
DROP TRIGGER dcm_change_audit ON dcm.record_indicator_values;
DROP TRIGGER dcm_change_audit ON dcm.records;
DROP TRIGGER dcm_change_audit ON dcm.indicators;
DROP TRIGGER dcm_change_audit ON dcm.documents;
DROP FUNCTION stm.log_dcm_change();
"""


class Migration(migrations.Migration):
    dependencies = [('pfbase', '0003_user_is_ib_operator_and_more')]

    operations = [
        migrations.AddField('securityevent', 'object_type', models.CharField(blank=True, db_index=True, max_length=64)),
        migrations.AddField('securityevent', 'object_id', models.PositiveBigIntegerField(blank=True, db_index=True, null=True)),
        migrations.AddField('securityevent', 'changed_fields', models.JSONField(blank=True, default=list)),
        migrations.AddField('securityevent', 'object_context', models.JSONField(blank=True, default=dict)),
        migrations.RunSQL(AUDIT_SQL, REVERSE_SQL),
    ]
