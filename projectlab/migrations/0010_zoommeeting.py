# Generated by Django 3.1.5 on 2021-04-05 12:27

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('projectlab', '0009_chatroom_chatroommessage'),
    ]

    operations = [
        migrations.CreateModel(
            name='ZoomMeeting',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('topic', models.CharField(max_length=200)),
                ('meeting_id', models.IntegerField()),
                ('meeting_passcode', models.CharField(max_length=200)),
                ('start_time', models.DateTimeField()),
                ('duration_min', models.IntegerField()),
                ('join_url', models.CharField(max_length=200)),
                ('project', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='projectlab.project')),
            ],
        ),
    ]
