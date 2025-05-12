from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [
        ('playbooks', '0002_playbook_tags'),
    ]

    operations = [
        migrations.AddField(
            model_name='playbook',
            name='playbook_type',
            field=models.CharField(max_length=10, choices=[('host','Host'),('group','Group')], default='group'),
        ),
    ]
