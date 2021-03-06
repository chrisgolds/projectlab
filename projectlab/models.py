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
	date_created = models.DateTimeField()
	timestamp = models.DateTimeField()
	file_path = models.CharField(max_length=200)
	current = models.BooleanField(default=True)
	next_workplace_id = models.IntegerField()
	last_workplace_id = models.IntegerField()