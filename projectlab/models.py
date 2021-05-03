'''
ProjectLab's design follows a convention influenced by the official Django tutorial.
"Writing your first Django app, part 1-4"
https://docs.djangoproject.com/en/3.2/intro/tutorial01/
https://docs.djangoproject.com/en/3.2/intro/tutorial02/
https://docs.djangoproject.com/en/3.2/intro/tutorial03/
https://docs.djangoproject.com/en/3.2/intro/tutorial04/
'''
from django.db import models
from django.contrib.auth.models import User

class Member(models.Model):
	usr = models.OneToOneField(User, on_delete=models.CASCADE)
	dob = models.DateField()
	university = models.CharField(max_length=200)

class Project(models.Model):
	members = models.ManyToManyField(Member)
	name = models.CharField(max_length=200)
	lead = models.CharField(max_length=200)
	deadline = models.DateField()

'''
Workspaces will have their 'current' value set to True by default
on the assumption that a new workspace becomes the active version after saving.
'next_workplace_id' was not removed during development and is not used
in the application's primary functionality
'''
class Workspace(models.Model):
	project = models.ForeignKey(Project, on_delete=models.CASCADE)
	name = models.CharField(max_length=200)
	user = models.CharField(max_length=200)
	save_desc = models.TextField()
	date_created = models.DateTimeField()
	timestamp = models.DateTimeField()
	file_path = models.CharField(max_length=200)
	current = models.BooleanField(default=True)
	next_workplace_id = models.IntegerField()
	last_workplace_id = models.IntegerField()

class Message(models.Model):
	workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE)
	user = models.CharField(max_length=200)
	timestamp = models.DateTimeField()
	body = models.TextField()

class Chatroom(models.Model):
	project = models.OneToOneField(Project, on_delete=models.CASCADE)

class ChatroomMessage(models.Model):
	chatroom = models.ForeignKey(Chatroom, on_delete=models.CASCADE)
	user = models.CharField(max_length=200)
	timestamp = models.DateTimeField()
	body = models.TextField()

class ZoomMeeting(models.Model):
	project = models.ForeignKey(Project, on_delete=models.CASCADE)
	topic = models.CharField(max_length=200)
	meeting_id = models.IntegerField()
	meeting_passcode = models.CharField(max_length=200)
	start_time = models.DateTimeField()
	duration_min = models.IntegerField()
	join_url = models.CharField(max_length=200)

class Log(models.Model):
	project = models.OneToOneField(Project, on_delete=models.CASCADE)

class LogMessage(models.Model):
	log = models.ForeignKey(Log, on_delete=models.CASCADE)
	log_type = models.CharField(max_length=200)
	user = models.CharField(max_length=200)
	timestamp = models.DateTimeField()
	body = models.TextField()