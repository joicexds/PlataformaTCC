"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from Model.base import Usuario
from django.db import connection

try:
    if 'core_usuario' in connection.introspection.table_names():
        if not Usuario.objects.filter(username='admin').exists():
            admin_user = Usuario.objects.create_superuser('admin', 'admin@admin.com', 'admin')
            admin_user.first_name = 'Administrador'
            admin_user.save()
            print("Usuário padrão 'admin' criado com sucesso.")
except Exception:
    pass

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('View.urls')),
]

from django.conf import settings
from django.conf.urls.static import static

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
