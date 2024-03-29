# Generated by Django 4.0.4 on 2022-04-16 18:41

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('control', '0010_jobartefact_mime_type'),
    ]

    operations = [
        migrations.AlterField(
            model_name='jobartefact',
            name='artefact_type',
            field=models.CharField(choices=[('SC', 'source'), ('IN', 'intermediate'), ('OU', 'output')], default='SC', max_length=4),
        ),
        migrations.AlterField(
            model_name='jobartefact',
            name='job',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='artefacts', to='control.gutenbergjob'),
        ),
    ]
