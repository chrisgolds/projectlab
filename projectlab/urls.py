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
    path('<str:acc>/project/<int:proj_id>/workspace/<int:workspace_id>/', views.view_workspace, name='view_workspace'),
    path('upload_file/<str:acc>/<int:proj_id>/<int:workspace_id>', views.upload_file, name='upload_file'),
    path('<str:acc>/project/<int:proj_id>/create_workspace/', views.create_workspace, name='create_workspace'),
    path('init_workspace/', views.init_workspace, name='init_workspace')
]