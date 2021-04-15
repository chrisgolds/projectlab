from django.contrib import admin

from .models import *

admin.site.register(Member)
admin.site.register(Project)
admin.site.register(Workspace)
admin.site.register(Message)
admin.site.register(Chatroom)
admin.site.register(ChatroomMessage)
admin.site.register(ZoomMeeting)