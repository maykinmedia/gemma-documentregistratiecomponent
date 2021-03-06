# Generated by Django 2.0.9 on 2018-12-19 13:25

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("datamodel", "0024_enkelvoudiginformatieobject_indicatie_gebruiksrecht")
    ]

    operations = [
        migrations.AddField(
            model_name="enkelvoudiginformatieobject",
            name="verzenddatum",
            field=models.DateField(
                blank=True,
                help_text="De datum waarop het INFORMATIEOBJECT verzonden is, zoals deze op het INFORMATIEOBJECT vermeld is. Dit geldt voor zowel inkomende als uitgaande INFORMATIEOBJECTen. Eenzelfde informatieobject kan niet tegelijk inkomend en uitgaand zijn.",
                null=True,
                verbose_name="verzenddatum",
            ),
        )
    ]
