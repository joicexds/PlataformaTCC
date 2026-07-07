import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Model.settings')
django.setup()

from Model.models import Usuario

def create_admin():
    if not Usuario.objects.filter(username='admin').exists():
        Usuario.objects.create_superuser('admin', 'admin@example.com', 'admin')
        print("Usuário 'admin' criado com sucesso com senha 'admin'.")
    else:
        print("Usuário 'admin' já existe.")

if __name__ == '__main__':
    create_admin()
