from django.urls import path

from . import views

app_name = "projectlab"
urlpatterns = [
    path('', views.login, name='login'),
    # path('verify_login/', views.verify_login, name='verify_login'),
    # path('sign_up/', views.sign_up, name='sign_up'),
    # path('verify_sign_up/', views.verify_sign_up, name='verify_sign_up'),
    # path('<username>/home/', views.home, name='home')
]