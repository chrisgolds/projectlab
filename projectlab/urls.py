from django.urls import path

from . import views

app_name = "projectlab"
urlpatterns = [
    path('', views.login, name='login'),
    path('verify_login/', views.verify_login, name='verify_login'),
    path('logout_user/', views.logout_user, name='logout_user'),
    path('verify_sign_up/', views.verify_sign_up, name='verify_sign_up'),
    path('search_user/', views.search_user, name='search_user'),
    path('<str:acc>/home/', views.home, name='home'),
    path('update_university/', views.update_university, name='update_university'),
    path('<str:acc>/create_project/', views.create_project, name='create_project'),
    path('init_project/', views.init_project, name='init_project'),
    path('<str:acc>/project/<int:proj_id>/', views.view_project, name='view_project'),
    path('<str:acc>/project/<int:proj_id>/log/', views.log, name='log'),
    path('<str:acc>/project/<int:proj_id>/workspace/<int:workspace_id>/', views.view_workspace, name='view_workspace'),
    path('upload_file/<str:acc>/<int:proj_id>/<int:workspace_id>/', views.upload_file, name='upload_file'),
    path('delete_file/', views.delete_file, name='delete_file'),
    path('<str:acc>/project/<int:proj_id>/create_workspace/', views.create_workspace, name='create_workspace'),
    path('init_workspace/', views.init_workspace, name='init_workspace'),
    path('save_workspace/', views.save_workspace, name='save_workspace'),
    path('<str:acc>/project/<int:proj_id>/workspace/<int:workspace_id>/history/', views.workspace_history, name='workspace_history'),
    path('<str:acc>/project/<int:proj_id>/edit_project/', views.edit_project, name='edit_project'),
    path('update_project/', views.update_project, name='update_project'),
    path('<str:acc>/project/<int:proj_id>/add_members/', views.add_members, name='add_members'),
    path('add_mem_to_proj/', views.add_mem_to_proj, name='add_mem_to_proj'),
    path('<str:acc>/project/<int:proj_id>/remove_members/', views.remove_members, name='remove_members'),
    path('rm_mem_from_proj/', views.rm_mem_from_proj, name='rm_mem_from_proj'),
    path('post_message/', views.post_message, name='post_message'),
    path('<str:acc>/project/<int:proj_id>/chat/', views.chat, name='chat'),
    path('check_chatroom/', views.check_chatroom, name='check_chatroom'),
    path('get_chatroom/', views.get_chatroom, name='get_chatroom'),
    path('post_chatroom/', views.post_chatroom, name='post_chatroom'),
    path('<str:acc>/project/<int:proj_id>/zoom_meetings/', views.zoom_meetings, name='zoom_meetings'),
    path('create_meeting/', views.create_meeting, name='create_meeting'),
    path('<str:acc>/project/<int:proj_id>/dashboard/', views.dashboard, name='dashboard'),
    path('get_user_chart/', views.get_user_chart, name='get_user_chart')
]