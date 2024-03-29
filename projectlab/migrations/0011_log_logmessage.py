# Generated by Django 3.1.5 on 2021-04-15 15:18

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('projectlab', '0010_zoommeeting'),
    ]

    operations = [
        migrations.CreateModel(
            name='Log',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('project', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to='projectlab.project')),
            ],
        ),
        migrations.CreateModel(
            name='LogMessage',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('log_type', models.CharField(max_length=200)),
                ('user', models.CharField(max_length=200)),
                ('timestamp', models.DateTimeField()),
                ('body', models.TextField()),
                ('log', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='projectlab.log')),
            ],
        ),
    ]
