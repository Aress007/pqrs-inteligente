from django.db import migrations


def eliminar_sentimiento(apps, schema_editor):
    """
    Elimina físicamente la columna sentimiento de pqrs_pqrs
    si todavía existe en la base de datos.
    """
    with schema_editor.connection.cursor() as cursor:
        columnas = schema_editor.connection.introspection.get_table_description(
            cursor,
            'pqrs_pqrs'
        )

        nombres = [columna.name for columna in columnas]

        if 'sentimiento' in nombres:
            schema_editor.execute(
                'ALTER TABLE pqrs_pqrs DROP COLUMN sentimiento'
            )


class Migration(migrations.Migration):

    dependencies = [
        ('pqrs', '0011_pqrs_fecha_cierre'),
    ]

    operations = [
        migrations.RunPython(
            eliminar_sentimiento,
            migrations.RunPython.noop,
        ),
    ]