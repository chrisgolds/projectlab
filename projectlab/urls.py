from django.urls import path

from . import views

app_name = "projectlab"
urlpatterns = [
    path('', views.login, name='login'),
    path('verify_login/', views.verify_login, name='verify_login'),
    path('verify_sign_up/', views.verify_sign_up, name='verify_sign_up'),
    path('<str:acc>/home/', views.home, name='home'),
    path('<str:acc>/create_project/', views.create_project, name='create_project')
]