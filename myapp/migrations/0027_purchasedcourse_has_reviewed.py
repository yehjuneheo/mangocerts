# Generated by Django 4.2.16 on 2024-11-20 20:13

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('myapp', '0026_certificationpost_practice_exam_translate_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='purchasedcourse',
            name='has_reviewed',
            field=models.BooleanField(default=False),
        ),
    ]
