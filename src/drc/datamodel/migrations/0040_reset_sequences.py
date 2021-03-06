# Generated by Django 2.2.2 on 2019-06-17 08:40
import os

from django.conf import settings
from django.db import migrations

INFILE = os.path.join(settings.BASE_DIR, "bin", "reset_sequences.sql")

with open(INFILE, "r") as infile:
    SQL = infile.read()


def reset_sequences(apps, schema_editor):
    # generate SQL for the reset
    with schema_editor.connection.cursor() as cursor:
        cursor.execute(SQL)
        rows = cursor.fetchall()

    sql = "\n".join(x[0] for x in rows)

    # execute the actual reset
    with schema_editor.connection.cursor() as cursor:
        cursor.execute(sql)


class Migration(migrations.Migration):

    dependencies = [("datamodel", "0039_auto_20190614_0839")]

    operations = [migrations.RunPython(reset_sequences, migrations.RunPython.noop)]
