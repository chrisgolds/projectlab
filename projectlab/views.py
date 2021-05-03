'''
ProjectLab's design follows a convention influenced by the official Django tutorial.
"Writing your first Django app, part 1-4"
https://docs.djangoproject.com/en/3.2/intro/tutorial01/
https://docs.djangoproject.com/en/3.2/intro/tutorial02/
https://docs.djangoproject.com/en/3.2/intro/tutorial03/
https://docs.djangoproject.com/en/3.2/intro/tutorial04/
'''
from django.http import QueryDict, HttpResponse, HttpResponseServerError, HttpResponseRedirect, JsonResponse
from django.core.exceptions import ObjectDoesNotExist
from django.shortcuts import render
from django.urls import reverse
from django.conf import settings
from django.contrib.auth.models import User
from django.core.files.storage import FileSystemStorage
from django.contrib.auth import authenticate
from django.contrib.auth import login as auth_login
from django.contrib.auth import logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.hashers import check_password
from django.utils import timezone
from django.db.models import Q
from io import BytesIO
import base64
import matplotlib.pyplot as plt
import jwt
import requests
import os
import shutil
import json
import re
import datetime
import time
import dateutil.parser
import universities

from .models import Member, Workspace, Project, Message, Chatroom, ChatroomMessage, ZoomMeeting, Log, LogMessage


def login(request):
	return render(request, 'projectlab/login.html')


# Verify credentials and log the user in
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


'''
More input validation, particularly checking if email belongs to a UK unviersity.
API calls made by the 'universities' package assigns university to profile based on domain.
If it cannot determine the university it will ask the user to select it from a dropdown on the home page.
'''
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


# Homepage lists user's projects by deadline in ascending order (earliest first)
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
				'all_projects' : user.project_set.all().order_by('deadline'),
				'today' : datetime.datetime.now(),
				'uni_names' : uni_names})
		else:
			return render(request, 'projectlab/home.html', {'user' : user,
				'all_projects' : user.project_set.all().order_by('deadline'),
				'today' : datetime.datetime.now()})
	else:
		return HttpResponseRedirect(reverse('projectlab:login'))


# Invoked when user selects uni from homepage should 'universities' be unable to determine the institution
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


'''
Function for creating a new project object.
Chatroom and Log objects created and assigned to the project.
Members added to project and log message created.
Main worksapces created for each member.
'''
def init_project(request):
	if request.method == "POST":
		proj_users = request.POST['users_arr'].split(",")
		new_proj = Project()
		new_proj.name = request.POST['project_name']
		new_proj.lead = request.POST['username']
		new_proj.deadline = datetime.datetime.strptime(request.POST['deadline'], "%d/%m/%Y").strftime("%Y-%m-%d")
		new_proj.save()

		chatroom = Chatroom(project = new_proj)
		chatroom.save()

		log = Log(project = new_proj)
		log.save() 

		for proj_username in proj_users:
			new_proj.members.add(Member.objects.get(usr = User.objects.get(username = proj_username)))
			new_proj.save()
			LogMessage(
				log = log,
				log_type = "add_member",
				user = request.POST['username'],
				timestamp = timezone.now(),
				body = request.POST['username'] + " added " + proj_username + " to the project"
			).save()

		for new_proj_user in new_proj.members.all():
			ws = Workspace()
			ws.project = new_proj
			ws.name = new_proj_user.usr.first_name + " - Main Workspace"
			ws.user = new_proj_user.usr.username
			ws.save_desc = ""
			ws.date_created = timezone.now()
			ws.timestamp = timezone.now()
			ws.file_path = str(new_proj.id) + "/"
			ws.next_workplace_id = -1
			ws.last_workplace_id = -1
			ws.save()

			ws.file_path += str(ws.id) + "/"
			ws.save()
			LogMessage(
				log = log,
				log_type = "create_workspace",
				user = request.POST['username'],
				timestamp = timezone.now(),
				body = request.POST['username'] + " created workspace " + ws.name + " for " + ws.user
			).save()


		return HttpResponse(reverse('projectlab:home', args=(request.POST["username"],)))


@login_required
def view_project(request, acc, proj_id):
	if acc == request.user.username:
		try:
			user = Member.objects.get(usr = User.objects.get(username = request.user.username))
			proj = user.project_set.get(id = proj_id)
			return render(request, 'projectlab/project.html', {'user' : user,
				'project' : proj,
				'log' : proj.log.logmessage_set.all().order_by('-timestamp')[:10]})
		except ObjectDoesNotExist:
			return render(request, 'projectlab/403.html', {'user' : user})
	else:
		return HttpResponseRedirect(reverse('projectlab:login'))


@login_required
def log(request, acc, proj_id):
	if acc == request.user.username:
		try:
			user = Member.objects.get(usr = User.objects.get(username = request.user.username))
			proj = user.project_set.get(id = proj_id)
			if user.usr.username != proj.lead:
				return render(request, 'projectlab/403.html', {'user' : user})
			return render(request, 'projectlab/log.html', {'user' : user,
				'project' : proj,
				'log' : proj.log.logmessage_set.all().order_by('-timestamp')})
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
			if not workspace.current:
				return render(request, 'projectlab/403.html', {'user' : user})
			fs = FileSystemStorage()
			files = fs.listdir(workspace.file_path)
			return render(request, 'projectlab/workspace.html', {'user' : user,
				'project' : proj,
				'workspace' : workspace,
				'messages' : workspace.message_set.all().order_by('-timestamp'),
				'files' : files[1],
				'location' : fs.base_url})
		except ObjectDoesNotExist:
			return render(request, 'projectlab/403.html', {'user' : user})
		except FileNotFoundError:
			return render(request, 'projectlab/workspace.html', {'user' : user,
				'project' : proj,
				'workspace' : workspace,
				'messages' : workspace.message_set.all().order_by('-timestamp'),
				'files' : []})
	else:
		return HttpResponseRedirect(reverse('projectlab:login'))


'''
Determines file path of workspace and uploads file to that directory using FileSystemStorage.
If file exists, current will be deleted and replaced with new version.
'''
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

				LogMessage(
					log = proj.log,
					log_type = "upload_file",
					user = user.usr.username,
					timestamp = timezone.now(),
					body = user.usr.username + " uploaded " + request.FILES["uploaded_file"].name + " to workspace " + workspace.name
				).save()

				return HttpResponseRedirect(reverse('projectlab:view_workspace', args=(acc,proj_id,workspace_id,)))
			except ObjectDoesNotExist:
				return render(request, 'projectlab/403.html', {'user' : user})
	else:
		return HttpResponseRedirect(reverse('projectlab:login'))


# Deletes provided file in request from provided workspace
def delete_file(request):
	if request.method == "PUT":
		try:
			res = QueryDict(request.body)
			ws = Workspace.objects.get(id = res.get("workspace_id"))
			fs = FileSystemStorage()
			fs.delete(ws.file_path + res.get("file"))

			LogMessage(
				log = ws.project.log,
				log_type = "delete_file",
				user = res.get("username"),
				timestamp = timezone.now(),
				body = res.get("username") + " deleted " + res.get("file") + " from workspace " + ws.name
			).save()

			return HttpResponse(reverse('projectlab:view_workspace', args=(res.get("username"),ws.project.id,ws.id,)))
		except:
			return HttpResponseServerError("Error updating project. Please try again.")


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


# Function for creating new Workspace
def init_workspace(request):
	if request.method == "POST":
		ws = Workspace()
		ws.project = Project.objects.get(id = int(request.POST['project_id']))
		ws.name = request.POST['workspace_name']
		ws.user = request.POST['username']
		ws.save_desc = ""
		ws.date_created = timezone.now()
		ws.timestamp = timezone.now()
		ws.file_path = request.POST['project_id'] + "/"
		ws.next_workplace_id = -1
		ws.last_workplace_id = -1
		ws.save()

		ws.file_path += str(ws.id) + "/"
		ws.save()
		LogMessage(
			log = ws.project.log,
			log_type = "create_workspace",
			user = request.POST['username'],
			timestamp = timezone.now(),
			body = request.POST['username'] + " created workspace " + ws.name
		).save()

		return HttpResponse(reverse('projectlab:view_workspace', args=(request.POST["username"],int(request.POST['project_id']),ws.id,)))


'''
Function for saving an existing Workspace.
Old workspace's 'current' status set to False, and provided save description assigned to 'save_desc'.
New workspace created with same name, user and messages.
Files from old workspace copied to file path of new one.
'''
def save_workspace(request):
	if request.method == "POST":
		ws_old = Workspace.objects.get(id=int(request.POST['last_workspace_id']))
		ws_old.current = False
		ws_old.save_desc = request.POST['save_desc']
		ws_old.save()

		ws = Workspace()
		ws.project = Project.objects.get(id = int(request.POST['project_id']))
		ws.name = request.POST['workspace_name']
		ws.user = request.POST['username']
		ws.date_created = timezone.now()
		ws.timestamp = timezone.now()
		ws.file_path = request.POST['project_id'] + "/"
		ws.next_workplace_id = -1
		ws.last_workplace_id = ws_old.id
		ws.save()
		for message in ws_old.message_set.all():
			message.workspace = ws
			message.save()

		ws.file_path += str(ws.id) + "/"
		ws.save()

		fs = FileSystemStorage()
		os.mkdir(os.path.join(settings.MEDIA_ROOT,ws.file_path))
		if fs.exists(ws_old.file_path):
			for file in fs.listdir(ws_old.file_path)[1]:
				shutil.copyfile(os.path.join(settings.MEDIA_ROOT,ws_old.file_path,file),os.path.join(settings.MEDIA_ROOT,ws.file_path,file))

		LogMessage(
			log = ws.project.log,
			log_type = "save_workspace",
			user = request.POST['username'],
			timestamp = timezone.now(),
			body = request.POST['username'] + " saved workspace " + ws.name
		).save()

		return HttpResponse(reverse('projectlab:view_workspace', args=(request.POST["username"],int(request.POST['project_id']),ws.id,)))


@login_required
def workspace_history(request, acc, proj_id, workspace_id):
	if acc == request.user.username:
		try:
			user = Member.objects.get(usr = User.objects.get(username = request.user.username))
			proj = user.project_set.get(id = proj_id)
			workspace = proj.workspace_set.get(id = workspace_id)
			if not workspace.current:
				return render(request, 'projectlab/403.html', {'user' : user})
			history = []
			fs = FileSystemStorage()
			id_current = workspace.last_workplace_id
			while id_current != -1:
				ws_current = Workspace.objects.get(id=id_current)
				history.append([ws_current, fs.listdir(ws_current.file_path)[1]])
				id_current = Workspace.objects.get(id=id_current).last_workplace_id
			return render(request, 'projectlab/workspace_history.html', {'user' : user,
				'project' : proj,
				'workspace' : workspace,
				'history' : history,
				'location' : fs.base_url})
		except ObjectDoesNotExist:
			return render(request, 'projectlab/403.html', {'user' : user})
	else:
		return HttpResponseRedirect(reverse('projectlab:login'))


@login_required
def edit_project(request, acc, proj_id):
	if acc == request.user.username:
		try:
			user = Member.objects.get(usr = User.objects.get(username = request.user.username))
			proj = user.project_set.get(id = proj_id)
			if user.usr.username != proj.lead:
				return render(request, 'projectlab/403.html', {'user' : user})
			return render(request, 'projectlab/edit_project.html', {'user' : user,
				'project' : proj,
				'deadline' : datetime.datetime.strptime(str(proj.deadline), "%Y-%m-%d").strftime("%d/%m/%Y")})
		except ObjectDoesNotExist:
			return render(request, 'projectlab/403.html', {'user' : user})
	else:
		return HttpResponseRedirect(reverse('projectlab:login'))


def update_project(request):
	if request.method == "PUT":
		try:
			res = QueryDict(request.body)
			proj = Project.objects.get(id = res.get("project_id"))
			if proj.name != res.get("project_name"):
				proj.name = res.get("project_name")
				proj.save()
			if proj.deadline != datetime.datetime.strptime(res.get("deadline"), "%d/%m/%Y").strftime("%Y-%m-%d"):
				proj.deadline = datetime.datetime.strptime(res.get("deadline"), "%d/%m/%Y").strftime("%Y-%m-%d")
				proj.save()
			return HttpResponse(reverse('projectlab:view_project', args=(res.get("username"),proj.id,)))
		except:
			return HttpResponseServerError("Error updating project. Please try again.")


@login_required
def add_members(request, acc, proj_id):
	if acc == request.user.username:
		try:
			user = Member.objects.get(usr = User.objects.get(username = request.user.username))
			proj = user.project_set.get(id = proj_id)
			if user.usr.username != proj.lead:
				return render(request, 'projectlab/403.html', {'user' : user})
			usernames = ""
			for username in proj.members.all():
				usernames += username.usr.username + ","
			return render(request, 'projectlab/add_members.html', {'user' : user,
				'project' : proj,
				'usernames' : usernames})
		except ObjectDoesNotExist:
			return render(request, 'projectlab/403.html', {'user' : user})
	else:
		return HttpResponseRedirect(reverse('projectlab:login'))


#Adding members creates a new main workspace for each one
def add_mem_to_proj(request):
	if request.method == "PUT":
		try:
			res = QueryDict(request.body)
			proj = Project.objects.get(id = res.get("project_id"))
			for member in res.get("users_arr").split(","):
				new_proj_user = Member.objects.get(usr = User.objects.get(username = member))

				proj.members.add(new_proj_user)
				proj.save()

				ws = Workspace()
				ws.project = proj
				ws.name = new_proj_user.usr.first_name + " - Main Workspace"
				ws.user = new_proj_user.usr.username
				ws.save_desc = ""
				ws.date_created = timezone.now()
				ws.timestamp = timezone.now()
				ws.file_path = str(proj.id) + "/"
				ws.next_workplace_id = -1
				ws.last_workplace_id = -1
				ws.save()

				ws.file_path += str(ws.id) + "/"
				ws.save()
				LogMessage(
					log = proj.log,
					log_type = "add_member",
					user = res.get("username"),
					timestamp = timezone.now(),
					body = res.get("username") + " added " + member + " to the project"
				).save()
			return HttpResponse(reverse('projectlab:view_project', args=(res.get("username"),proj.id,)))
		except:
			return HttpResponseServerError("Error updating project. Please try again.")


@login_required
def remove_members(request, acc, proj_id):
	if acc == request.user.username:
		try:
			user = Member.objects.get(usr = User.objects.get(username = request.user.username))
			proj = user.project_set.get(id = proj_id)
			if user.usr.username != proj.lead:
				return render(request, 'projectlab/403.html', {'user' : user})
			return render(request, 'projectlab/remove_members.html', {'user' : user,
				'project' : proj})
		except ObjectDoesNotExist:
			return render(request, 'projectlab/403.html', {'user' : user})
	else:
		return HttpResponseRedirect(reverse('projectlab:login'))


# Removing members deletes all associated workspaces and their files
def rm_mem_from_proj(request):
	if request.method == "PUT":
		try:
			res = QueryDict(request.body)
			proj = Project.objects.get(id = res.get("project_id"))
			for member in res.get("users_arr").split(","):
				rm_proj_user_ws = proj.workspace_set.filter(user=member)
				for ws in rm_proj_user_ws:
					fs = FileSystemStorage()
					if fs.exists(ws.file_path):
						for file in fs.listdir(ws.file_path)[1]:
							fs.delete(ws.file_path + file)
					ws.delete()

				proj.members.remove(Member.objects.get(usr = User.objects.get(username = member)))
				LogMessage(
					log = proj.log,
					log_type = "remove_member",
					user = res.get("username"),
					timestamp = timezone.now(),
					body = res.get("username") + " removed " + member + " from the project"
				).save()
			return HttpResponse(reverse('projectlab:view_project', args=(res.get("username"),proj.id,)))
		except ObjectDoesNotExist:
			return render(request, 'projectlab/403.html', {'user' : user})
		except:
			return HttpResponseServerError("Error updating project. Please try again.")


def post_message(request):
	if request.method == "POST":
		msg = Message()
		ws = Workspace.objects.get(id = int(request.POST['workspace_id']))
		msg.workspace = ws
		msg.user = request.POST['username']
		msg.timestamp = timezone.now()
		msg.body = request.POST['body']
		msg.save()

		LogMessage(
			log = ws.project.log,
			log_type = "post_message",
			user = request.POST['username'],
			timestamp = timezone.now(),
			body = request.POST['username'] + " posted a message to " + ws.name
		).save()

		return HttpResponse(reverse('projectlab:view_workspace', args=(request.POST["username"],ws.project.id,ws.id,)))


@login_required
def chat(request, acc, proj_id):
	if acc == request.user.username:
		try:
			user = Member.objects.get(usr = User.objects.get(username = request.user.username))
			proj = user.project_set.get(id = proj_id)
			return render(request, 'projectlab/chat.html', {'user' : user,
				'project' : proj,
				'chatroom' : proj.chatroom.chatroommessage_set.all().order_by('-timestamp')})
		except ObjectDoesNotExist:
			return render(request, 'projectlab/403.html', {'user' : user})
	else:
		return HttpResponseRedirect(reverse('projectlab:login'))


def check_chatroom(request):
	if request.method == "GET":
		return JsonResponse({'len' : len(Chatroom.objects.get(project = Project.objects.get(id = request.GET["project"])).chatroommessage_set.all())})


def get_chatroom(request):
	if request.method == "GET":
		chatroom = Chatroom.objects.get(project = Project.objects.get(id = request.GET["project"]))
		res = {'data' : []}
		for chat in chatroom.chatroommessage_set.all().order_by('-timestamp'):
			res['data'].append({'user' : chat.user, 'timestamp' : chat.timestamp.strftime("%d-%m-%Y %H:%M"), 'body' : chat.body})
		return JsonResponse(res)


def post_chatroom(request):
	if request.method == "POST":
		room = Chatroom.objects.get(project = Project.objects.get(id = request.POST["project"]))
		chat_msg = ChatroomMessage()
		chat_msg.chatroom = room
		chat_msg.user = request.POST["username"]
		chat_msg.timestamp = timezone.now()
		chat_msg.body = request.POST["body"]
		chat_msg.save()

		return JsonResponse({'status' : 200})


@login_required
def zoom_meetings(request, acc, proj_id):
	if acc == request.user.username:
		try:
			user = Member.objects.get(usr = User.objects.get(username = request.user.username))
			proj = user.project_set.get(id = proj_id)
			return render(request, 'projectlab/zoom_meetings.html', {'user' : user,
				'project' : proj,
				'meetings' : proj.zoommeeting_set.all().order_by('start_time'),
				'today' : datetime.datetime.now()})
		except ObjectDoesNotExist:
			return render(request, 'projectlab/403.html', {'user' : user})
	else:
		return HttpResponseRedirect(reverse('projectlab:login'))


''' 
Creates new Zoom meeting.
Generates JWT token based on provided API key and secret key.
Populates header and data appropriately before sending POST request to api.zoom.us.
Response data assigned to a new Zoom meeting object.
Code sampled from https://jwt.io [accessed 03/05/21]
'''
def create_meeting(request):
	if request.method == "POST":
		header = {"alg": "HS256", "typ": "JWT"}
		payload = {"iss": request.POST["api_key"], "exp": int(time.time() + 3600)}
		token = jwt.encode(payload, request.POST["secret_key"], algorithm="HS256", headers=header).decode("utf-8")
		
		headers = {
			'content-type': "application/json",
			"Authorization": ("Bearer " + str(token))
		}
		url = "https://api.zoom.us/v2/users/me/meetings"

		data = {
			"topic" : request.POST["topic"],
			"type" : 2,
			"start_time" : datetime.datetime.strptime(request.POST['start_date'], "%d/%m/%Y").strftime("%Y-%m-%d") + "T" + request.POST['start_time'] + ":00",
			"duration" : int(request.POST["duration"]),
			"timezone" : "GMT"
		}

		res = requests.post(url, data=json.dumps(data), headers=headers)
		if res.status_code >= 201 and res.status_code < 300:
			json_res = json.loads(res.text)

			zm = ZoomMeeting()
			zm.project = Project.objects.get(id = request.POST["project"])
			zm.topic = json_res['topic']
			zm.meeting_id = int(json_res['id'])
			zm.meeting_passcode = json_res['password']
			zm.start_time = dateutil.parser.parse(json_res['start_time'])
			zm.duration_min = json_res['duration']
			zm.join_url = json_res['join_url']

			zm.save()

			LogMessage(
				log = zm.project.log,
				log_type = "zoom_meeting",
				user = request.POST['username'],
				timestamp = timezone.now(),
				body = request.POST['username'] + " created a Zoom meeting for " + str(zm.start_time)
			).save()

			return HttpResponse(reverse('projectlab:zoom_meetings', args=(request.POST["username"],request.POST["project"],)))
		else:
			return HttpResponseServerError("Error creating Zoom meeting. Ensure you have used the correct API and secret keys and try again.")


'''
Dashboard page creates plots for total collaboration summary and timeline of collaborations by each member.
Plots generated using 'matplotlib'.
Watermarks added to plots to preserve integrity.
Code sampled from https://matplotlib.org/stable/gallery/pie_and_polar_charts/pie_features.html [accessed 03/05/21]
'''
@login_required
def dashboard(request, acc, proj_id):
	if acc == request.user.username:
		try:
			user = Member.objects.get(usr = User.objects.get(username = request.user.username))
			proj = user.project_set.get(id = proj_id)
			if user.usr.username != proj.lead:
				return render(request, 'projectlab/403.html', {'user' : user})

			labels = []
			sizes = []

			for member in proj.members.all():
				labels.append(member.usr.username)
				sizes.append(len(proj.log.logmessage_set.filter(user=member.usr.username)))

			plt.title(proj.name)
			plt.pie(sizes, autopct='%1.2f%%')
			plt.legend(labels, loc="lower center", bbox_to_anchor=(0.5, -0.3), ncol=3)
			plt.tight_layout()
			plt.text(0.95, 0.05, 'ProjectLab',fontsize=50,color='gray',ha='right',va='bottom',alpha=0.5)
			plt.text(-1, -1.2, 'Generated ' + str(datetime.datetime.now().day) + "/" + str(datetime.datetime.now().month) + "/" + str(datetime.datetime.now().year),fontsize=7,color='black')
			plt.axis('equal')

			buff = BytesIO()
			plt.savefig(buff, format='png')
			buff.seek(0)
			plot_img = buff.getvalue()
			buff.close()

			plt.close()

			plot = base64.b64encode(plot_img)
			plot = plot.decode('utf-8')


			for member in proj.members.all():
				date_count = {}
				for log_message in proj.log.logmessage_set.filter(user=member.usr.username):
					date = str(log_message.timestamp.day) + "/" + str(log_message.timestamp.month) + "/" + str(log_message.timestamp.year)
					if date not in date_count:
						date_count[date] = 0
						date_count[date] += 1
					else:
						date_count[date] += 1
				x_vals = list(date_count.keys())
				y_vals = list(date_count.values())
				plt.plot(x_vals, y_vals, marker="o")

			plt.title(proj.name)
			plt.legend(labels, loc="lower center", bbox_to_anchor=(0.5, -0.3), ncol=3)
			plt.tight_layout()

			buff = BytesIO()
			plt.savefig(buff, format='png')
			buff.seek(0)
			plot_img = buff.getvalue()
			buff.close()

			plt.close()

			plot_line = base64.b64encode(plot_img)
			plot_line = plot_line.decode('utf-8')

			return render(request, 'projectlab/dashboard.html', {'user' : user,
	        	'project' : proj,
	        	'plot' : plot,
	        	'plot_line' : plot_line})


		except ObjectDoesNotExist:
			return render(request, 'projectlab/403.html', {'user' : user})
	else:
		return HttpResponseRedirect(reverse('projectlab:login'))


# Retrieves summary of collaborations for provided user
def get_user_chart(request):
	if request.method == "GET":
		try:
			user = Member.objects.get(usr = User.objects.get(username = request.GET["user"]))
			proj = user.project_set.get(id = request.GET["project"])

			labels = []
			sizes = []

			colors = [
				"#a4a4f4",
				"#1c1ce3",
				"#80ffaa",
				"#00cc44",
				"#ff8566",
				"#e62e00"
			]

			types = {
				'create_workspace' : "Created workspace",
				'upload_file' : "Uploaded file",
				'delete_file' : "Deleted file",
				'save_workspace' : "Saved workspace",
				'post_message' : "Posted message to workspace",
				'zoom_meeting' : "Created Zoom meeting"
			}

			for key, val in types.items():
				labels.append(val)
				sizes.append(len(proj.log.logmessage_set.filter(user=user.usr.username).filter(log_type=key)))

			if not sizes:
				return HttpResponseServerError("ERROR: Could not produce chart.")

			plt.title(user.usr.username + " - " + proj.name)
			plt.pie(sizes, autopct='%1.2f%%', colors=colors)
			plt.legend(labels, loc="lower center", bbox_to_anchor=(0.5, -0.3), ncol=3)
			plt.tight_layout()
			plt.text(0.95, 0.05, 'ProjectLab',fontsize=50,color='gray',ha='right',va='bottom',alpha=0.5)
			plt.text(-1, -1.2, 'Generated ' + str(datetime.datetime.now().day) + "/" + str(datetime.datetime.now().month) + "/" + str(datetime.datetime.now().year),fontsize=7,color='black')
			plt.axis('equal')

			buff = BytesIO()
			plt.savefig(buff, format='png')
			buff.seek(0)
			plot_img = buff.getvalue()
			buff.close()

			plt.close()

			plot = base64.b64encode(plot_img)
			plot = plot.decode('utf-8')

			return HttpResponse(plot)

		except Exception:
			return HttpResponseServerError("ERROR: Could not produce chart.")