# Generated by Django 5.2.1 on 2025-06-16 03:57

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('agendamentos', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='agendamento',
            name='data_hora',
            field=models.DateTimeField(),
        ),
    ]
