from django.http import QueryDict, HttpResponse, HttpResponseServerError, HttpResponseRedirect, JsonResponse
from django.core.exceptions import ObjectDoesNotExist
from django.shortcuts import render
from django.urls import reverse
from django.contrib.auth.models import User
from django.core.files.storage import FileSystemStorage
from django.contrib.auth import authenticate
from django.contrib.auth import login as auth_login
from django.contrib.auth import logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.hashers import check_password
from django.utils import timezone
import os
import json
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


def logout_user(request):
	auth_logout(request)
	return HttpResponseRedirect(reverse('projectlab:login'))

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
				selected_uni = ""
				uni = list(universities.API().search(domain = domain.group()))
				if uni:
					selected_uni = uni[0].name
				Member(
					usr = User.objects.create_user(
							username = request.POST['signup_username'],
							password = request.POST['signup_password'],
							email = request.POST['email'],
							first_name = request.POST['firstName'],
							last_name = request.POST['lastName']
					),
					dob = datetime.datetime.strptime(request.POST['dob'], "%d/%m/%Y").strftime("%Y-%m-%d"),
					university = selected_uni
				).save()
				return HttpResponse("<strong>Sign up successful!<strong>")
			else:
				return HttpResponseServerError("<strong>The email address you have provided is already in use. Please try another address<strong>")
		else:
			return HttpResponseServerError("<strong>The username you have provided is already in use. Please try another name<strong>")


def search_user(request):
	if request.method == "GET":
		try:
			result = None
			if "@" in request.GET["user_search"]:
				result = Member.objects.get(usr = User.objects.get(email = request.GET["user_search"]))
			else:
				result = Member.objects.get(usr = User.objects.get(username = request.GET["user_search"]))
			return JsonResponse({'status' : 200,
				'data' : {
					'username' : result.usr.username,
					'email' : result.usr.email,
					'first_name' : result.usr.first_name,
					'last_name' : result.usr.last_name,
					'dob' : result.dob,
					'university' : result.university
				}
			})
		except ObjectDoesNotExist:
			return JsonResponse({'status' : 500,
				'message' : 'User with username or email does not exist'
			})


@login_required
def home(request, acc):
	if acc == request.user.username:
		user = Member.objects.get(usr = User.objects.get(username = request.user.username))
		if user.university == "":
			unis = list(universities.API().search(country = "United Kingdom"))
			uni_names = []
			for uni in unis:
				uni_names.append(uni.name)
			return render(request, 'projectlab/home.html', {'user' : user,
				'uni_names' : uni_names})
		else:
			return render(request, 'projectlab/home.html', {'user' : user})
	else:
		return HttpResponseRedirect(reverse('projectlab:login'))


def update_university(request):
	if request.method == "PUT":
		try:
			res = QueryDict(request.body)
			user = Member.objects.get(usr = User.objects.get(username = res.get("username")))
			user.university = res.get("uni")
			user.save()
			return HttpResponse(reverse('projectlab:home', args=(user.usr.username,)))
		except:
			return HttpResponseServerError("Error updating university. Please try again.")


@login_required
def create_project(request, acc):
	if acc == request.user.username:
		user = Member.objects.get(usr = User.objects.get(username = request.user.username))
		return render(request, 'projectlab/create_project.html', {'user' : user})
	else:
		return HttpResponseRedirect(reverse('projectlab:login'))


def init_project(request):
	if request.method == "POST":
		proj_users = request.POST['users_arr'].split(",")
		new_proj = Project()
		new_proj.name = request.POST['project_name']
		new_proj.lead = request.POST['username']
		new_proj.deadline = datetime.datetime.strptime(request.POST['deadline'], "%d/%m/%Y").strftime("%Y-%m-%d")
		new_proj.save()

		for proj_username in proj_users:
			new_proj.members.add(Member.objects.get(usr = User.objects.get(username = proj_username)))
			new_proj.save()

		for new_proj_user in new_proj.members.all():
			ws = Workspace()
			ws.project = new_proj
			ws.name = new_proj_user.usr.first_name + " - Main Workspace"
			ws.user = new_proj_user.usr.username
			ws.date_created = timezone.now()
			ws.timestamp = timezone.now()
			ws.file_path = str(new_proj.id) + "/"
			ws.next_workplace_id = -1
			ws.last_workplace_id = -1
			ws.save()

			ws.file_path += str(ws.id) + "/"
			ws.save()

		return HttpResponse(reverse('projectlab:home', args=(request.POST["username"],)))


@login_required
def view_project(request, acc, proj_id):
	if acc == request.user.username:
		try:
			user = Member.objects.get(usr = User.objects.get(username = request.user.username))
			proj = user.project_set.get(id = proj_id)
			return render(request, 'projectlab/project.html', {'user' : user,
				'project' : proj})
		except ObjectDoesNotExist:
			return render(request, 'projectlab/403.html', {'user' : user})
	else:
		return HttpResponseRedirect(reverse('projectlab:login'))


@login_required
def view_workspace(request, acc, proj_id, workspace_id):
	if acc == request.user.username:
		try:
			user = Member.objects.get(usr = User.objects.get(username = request.user.username))
			proj = user.project_set.get(id = proj_id)
			workspace = proj.workspace_set.get(id = workspace_id)
			fs = FileSystemStorage()
			files = fs.listdir(workspace.file_path)
			return render(request, 'projectlab/workspace.html', {'user' : user,
				'project' : proj,
				'workspace' : workspace,
				'files' : files[1],
				'location' : fs.base_url})
		except ObjectDoesNotExist:
			return render(request, 'projectlab/403.html', {'user' : user})
		except FileNotFoundError:
			return render(request, 'projectlab/workspace.html', {'user' : user,
				'project' : proj,
				'workspace' : workspace,
				'files' : []})
	else:
		return HttpResponseRedirect(reverse('projectlab:login'))


@login_required
def upload_file(request, acc, proj_id, workspace_id):
	if acc == request.user.username:
		if request.method == 'POST' and request.FILES:
			try:
				user = Member.objects.get(usr = User.objects.get(username = request.user.username))
				proj = user.project_set.get(id = proj_id)
				workspace = proj.workspace_set.get(id = workspace_id)
				fs = FileSystemStorage()
				if fs.exists(workspace.file_path + request.FILES["uploaded_file"].name):
					fs.delete(workspace.file_path + request.FILES["uploaded_file"].name)
				fs.save(workspace.file_path + request.FILES["uploaded_file"].name, request.FILES["uploaded_file"])
				workspace.timestamp = timezone.now()
				workspace.save()
				return HttpResponseRedirect(reverse('projectlab:view_workspace', args=(acc,proj_id,workspace_id,)))
			except ObjectDoesNotExist:
				return render(request, 'projectlab/403.html', {'user' : user})
	else:
		return HttpResponseRedirect(reverse('projectlab:login'))


@login_required
def create_workspace(request, acc, proj_id):
	if acc == request.user.username:
		try:
			user = Member.objects.get(usr = User.objects.get(username = request.user.username))
			proj = user.project_set.get(id = proj_id)
			return render(request, 'projectlab/create_workspace.html', {'user' : user,
				'project' : proj})
		except ObjectDoesNotExist:
			return render(request, 'projectlab/403.html', {'user' : user})
	else:
		return HttpResponseRedirect(reverse('projectlab:login'))


def init_workspace(request):
	if request.method == "POST":
		ws = Workspace()
		ws.project = Project.objects.get(id = int(request.POST['project_id']))
		ws.name = request.POST['workspace_name']
		ws.user = request.POST['username']
		ws.date_created = timezone.now()
		ws.timestamp = timezone.now()
		ws.file_path = request.POST['project_id'] + "/"
		ws.next_workplace_id = -1
		ws.last_workplace_id = -1
		ws.save()

		ws.file_path += str(ws.id) + "/"
		ws.save()

		return HttpResponse(reverse('projectlab:home', args=(request.POST["username"],)))