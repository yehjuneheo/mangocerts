# Generated by Django 4.2.16 on 2024-11-05 22:18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('myapp', '0009_certificationpost_number_of_practices'),
    ]

    operations = [
        migrations.AlterField(
            model_name='certificationpost',
            name='number_of_practices',
            field=models.CharField(default='4', max_length=10),
        ),
    ]
