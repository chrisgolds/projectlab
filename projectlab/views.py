from django.http import HttpResponse, HttpResponseServerError, HttpResponseRedirect
from django.core.exceptions import ObjectDoesNotExist
from django.shortcuts import render
from django.urls import reverse
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from django.contrib.auth import login as auth_login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.hashers import check_password
import os
import re
import datetime
import universities

from .models import Member, Workspace, Project

def login(request):
	return render(request, 'projectlab/login.html')

def verify_login(request):
	try:
		account = Member.objects.get(usr = User.objects.get(username = request.POST['username']))
	except ObjectDoesNotExist:
		return render(request, 'projectlab/login.html', {
				'error_with_sign_in' : True
			})
	else:
		if not check_password(request.POST['password'], account.usr.password):
			return render(request, 'projectlab/login.html', {
					'error_with_sign_in' : True
				})
		user = authenticate(username=account.usr.username, password=request.POST['password'])
		if user is not None:
			if user.is_active:
				request.session.set_expiry(0)
				auth_login(request, user)
				return HttpResponseRedirect(reverse('projectlab:home', args=(account.usr.username,)))


def verify_sign_up(request):
	if request.method == "POST":
		try:
			username = Member.objects.get(usr = User.objects.get(username = request.POST['signup_username']))
		except ObjectDoesNotExist:

			try:
				email = Member.objects.get(usr = User.objects.get(email = request.POST['email']))
			except ObjectDoesNotExist:
				addr = request.POST['email'].split('@')[1]
				domain = re.search("\w+.ac.uk$", addr)
				if not domain:
					return HttpResponseServerError("<strong>The email address you have provided does not belong to a valid institution<strong>")
				uni = list(universities.API().search(domain = domain.group()))
				if not uni:
					return HttpResponseServerError("<strong>The email address you have provided does not belong to a valid institution<strong>")
				else:
					Member(
						usr = User.objects.create_user(
								username = request.POST['signup_username'],
								password = request.POST['signup_password'],
								email = request.POST['email'],
								first_name = request.POST['firstName'],
								last_name = request.POST['lastName']
						),
						dob = datetime.datetime.strptime(request.POST['dob'], "%d/%m/%Y").strftime("%Y-%m-%d"),
						university = uni[0].name
					).save()
					return HttpResponse("<strong>Sign up successful!<strong>")
			else:
				return HttpResponseServerError("<strong>The email address you have provided is already in use. Please try another address<strong>")
		else:
			return HttpResponseServerError("<strong>The username you have provided is already in use. Please try another name<strong>")


@login_required
def home(request, acc):
	if acc == request.user.username:
		user = Member.objects.get(usr = User.objects.get(username = request.user.username))
		return render(request, 'projectlab/home.html', {'user' : user,
			'projects' : user.project_set.all()})
	else:
		return HttpResponseRedirect(reverse('projectlab:login'))


@login_required
def create_project(request, acc):
	if acc == request.user.username:
		print("Here")
		#TODO - Form for creating new project
		
	else:
		return HttpResponseRedirect(reverse('projectlab:login'))