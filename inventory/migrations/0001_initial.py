# Generated by Django 5.0.14 on 2025-05-07 19:18

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Environment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255, unique=True)),
                ('description', models.TextField(blank=True, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='Group',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255, unique=True)),
                ('type', models.CharField(max_length=255)),
                ('description', models.TextField(blank=True, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='Host',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255, unique=True)),
                ('ip', models.GenericIPAddressField(unique=True)),
                ('operating_system', models.CharField(max_length=255)),
                ('ansible_python_interpreter', models.CharField(max_length=255)),
                ('status', models.CharField(max_length=255)),
                ('tags', models.TextField(blank=True, null=True)),
                ('notes', models.TextField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('environment', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='inventory.environment')),
                ('group', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='inventory.group')),
            ],
        ),
    ]
