from django.http import HttpResponse, HttpResponseRedirect
from django.core.exceptions import ObjectDoesNotExist
from django.shortcuts import render
from django.urls import reverse

from .models import Member, Workspace, Project

def login(request):
	return render(request, 'projectlab/login.html')

def verify_login(request):
	print(request)

def verify_sign_up(request):
	print(request)