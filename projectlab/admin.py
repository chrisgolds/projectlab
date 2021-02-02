from django.contrib import admin

from .models import *

admin.site.register(Member)
admin.site.register(Project)
#admin.site.register(Workspace)