from django.urls import path

from . import views

app_name = "projectlab"
urlpatterns = [
    path('', views.login, name='login'),
    path('verify_login/', views.verify_login, name='verify_login'),
    path('verify_sign_up/', views.verify_sign_up, name='verify_sign_up'),
    path('search_user/', views.search_user, name='search_user'),
    path('<str:acc>/home/', views.home, name='home'),
    path('update_university/', views.update_university, name='update_university'),
    path('<str:acc>/create_project/', views.create_project, name='create_project'),
    path('init_project/', views.init_project, name='init_project')
]