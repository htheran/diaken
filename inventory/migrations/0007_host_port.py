# Generated by Django 4.2.21 on 2025-05-14 15:20

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0006_remove_host_ansible_become_password_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='host',
            name='port',
            field=models.IntegerField(blank=True, help_text='SSH port for connection', null=True),
        ),
    ]
