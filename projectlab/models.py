from django.db import models
from django.contrib.auth.models import User

class Member(models.Model):
	usr = models.OneToOneField(User, on_delete=models.CASCADE)
	firstName = models.CharField(max_length=200)
	lastName = models.CharField(max_length=200)
	dob = models.DateField()
	university = models.CharField(max_length=200)

class Workspace(models.Model):
	member = models.OneToOneField(Member, on_delete=models.CASCADE)
	project = models.ForeignKey('Project', on_delete=models.CASCADE)
	name = models.CharField(max_length=200)
	file_path = models.CharField(max_length=200)
	next_workplace_id = models.IntegerField()
	last_workplace_id = models.IntegerField()

class Project(models.Model):
	members = models.ManyToMany(Member)
	name = models.CharField(max_length=200)
	deadline = models.DateField()