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
import datetime

from .models import Member, Workspace, Project

def login(request):
	unis = []
	file = open(os.path.join(os.path.dirname(__file__), 'uni.txt'))
	for line in file:
		unis.append(line.split("\t")[2])
	return render(request, 'projectlab/login.html', {'unis' : unis})

def verify_login(request):
	try:
		account = Member.objects.get(usr = User.objects.get(username = request.POST['username']))
	except ObjectDoesNotExist:
		unis = []
		file = open(os.path.join(os.path.dirname(__file__), 'uni.txt'))
		for line in file:
			unis.append(line.split("\t")[2])
		return render(request, 'projectlab/login.html', {
				'error_with_sign_in' : True,
				'unis' : unis
			})
	else:
		if not check_password(request.POST['password'], account.usr.password):
			unis = []
			file = open(os.path.join(os.path.dirname(__file__), 'uni.txt'))
			for line in file:
				unis.append(line.split("\t")[2])
			return render(request, 'projectlab/login.html', {
					'error_with_sign_in' : True,
					'unis' : unis
				})
		user = authenticate(username=account.usr.username, password=request.POST['password'])
		if user is not None:
			if user.is_active:
				request.session.set_expiry(20)
				auth_login(request, user)
				args = str(account.id) + "_" + account.usr.username
				return HttpResponseRedirect(reverse('projectlab:home', args=(args,)))


def verify_sign_up(request):
	if request.method == "POST":
		try:
			username = Member.objects.get(usr = User.objects.get(username = request.POST['signup_username']))
		except ObjectDoesNotExist:
			Member(
				usr = User.objects.create_user(
						username = request.POST['signup_username'],
						password = request.POST['signup_password'],
						email = request.POST['email'],
						first_name = request.POST['firstName'],
						last_name = request.POST['lastName']
					),
				dob = datetime.datetime.strptime(request.POST['dob'], "%d/%m/%Y").strftime("%Y-%m-%d"),
				university = request.POST['university']
			).save()
			return HttpResponse("<strong>Sign up successful!<strong>")
		else:
			return HttpResponseServerError("<strong>The username you have provided is already in use. Please try another name<strong>")


@login_required
def home(request, acc):
	verify = acc.split('_')
	user = Member.objects.get(id = int(verify[0]))
	if user.usr.username == verify[1]:
		return render(request, 'projectlab/home.html', {'user' : user})