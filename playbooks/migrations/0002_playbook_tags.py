from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [
        ('playbooks', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='playbook',
            name='tags',
            field=models.CharField(max_length=255, blank=True, null=True, help_text='Etiquetas separadas por coma, ej: group,host'),
        ),
    ]
