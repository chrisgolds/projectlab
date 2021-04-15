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
