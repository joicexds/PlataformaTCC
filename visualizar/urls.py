from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('', views.CustomLoginView.as_view(), name='login'),
    path('home/', views.home, name='home'),
    path('explorar-profissoes/', views.explorar_profissoes, name='explorar_profissoes'),
    path('perfil/', views.profile, name='profile'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),
    path('register/', views.register, name='register'),
    path('teste/iniciar/', views.iniciar_teste, name='iniciar_teste'),
    path('teste/responder/', views.responder_teste, name='responder_teste'),
    path('teste/resultado/', views.resultado_teste, name='resultado_teste'),
]
