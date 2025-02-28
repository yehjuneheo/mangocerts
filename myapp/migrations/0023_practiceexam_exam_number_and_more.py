# Generated by Django 4.2.16 on 2024-11-09 02:20

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('myapp', '0022_alter_certificationpost_number_of_practices_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='practiceexam',
            name='exam_number',
            field=models.IntegerField(default=1),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='userexamprogress',
            name='course',
            field=models.ForeignKey(default=2, on_delete=django.db.models.deletion.CASCADE, to='myapp.certificationpost'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='userexamprogress',
            name='exam',
            field=models.ForeignKey(default=3, on_delete=django.db.models.deletion.CASCADE, to='myapp.practiceexam'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='userexamprogress',
            name='user',
            field=models.ForeignKey(default=4, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
            preserve_default=False,
        ),
    ]
