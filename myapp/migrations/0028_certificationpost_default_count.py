# Generated by Django 4.2.16 on 2024-11-20 23:42

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('myapp', '0027_purchasedcourse_has_reviewed'),
    ]

    operations = [
        migrations.AddField(
            model_name='certificationpost',
            name='default_count',
            field=models.IntegerField(default=4),
        ),
    ]