# Generated by Django 2.1.5 on 2019-01-11 06:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('doc_scanner', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='source',
            name='source_name',
            field=models.CharField(default=None, max_length=100),
        ),
    ]
