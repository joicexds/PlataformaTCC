from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

class Command(BaseCommand):
    help = "Cria um superusuário padrão para acesso ao painel Django."

    def handle(self, *args, **options):
        User = get_user_model()
        username = "admin"
        email = ""
        password = "12345678"

        if User.objects.filter(username=username).exists():
            self.stdout.write(self.style.WARNING(f"Usuário '{username}' já existe. Nenhuma ação foi tomada."))
            return

        User.objects.create_superuser(username=username, email=email, password=password)
        self.stdout.write(self.style.SUCCESS("Superusuário criado com sucesso!"))
        self.stdout.write(self.style.SUCCESS(f"Login: {username}"))
        self.stdout.write(self.style.SUCCESS(f"Senha: {password}"))
