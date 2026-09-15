from django import forms
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
import re
from django.utils.text import slugify as _slugify

class RegisterForm(forms.Form):

    full_name = forms.CharField(
        label="Nome Completo",
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Digite seu nome completo',
            'required': True
        })
    )
    password = forms.CharField(
        label="Senha",
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Digite sua senha',
            'required': True
        })
    )
    password_confirm = forms.CharField(
        label="Confirmar Senha",
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirme sua senha',
            'required': True
        })
    )



    def clean_password(self):
        password = self.cleaned_data.get('password')
        if password:
            # Exigência de senha simples: exatamente 8 dígitos numéricos
            if not password.isdigit() or len(password) != 8:
                raise ValidationError('A senha deve conter exatamente 8 dígitos numéricos.')
        return password

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        password_confirm = cleaned_data.get("password_confirm")

        if password and password_confirm and password != password_confirm:
            self.add_error('password_confirm', "As senhas não coincidem.")
        return cleaned_data

    def save(self):
        full_name = self.cleaned_data.get('full_name')
        password = self.cleaned_data.get('password')

        # Split full_name into first_name and last_name
        parts = full_name.strip().split(' ', 1)
        first_name = _slugify(parts[0])
        last_name = _slugify(parts[1]) if len(parts) > 1 else ''

        # Build username
        username = f"{first_name}_{last_name}" if last_name else first_name
        base_username = username
        counter = 1
        while User.objects.filter(username=username).exists():
            username = f"{base_username}{counter}"
            counter += 1

        user = User.objects.create_user(
            username=username,
            email='',
            password=password,
            first_name=first_name,
            last_name=last_name,
        )
        return user


from .models import UserProfile

class UserProfileForm(forms.ModelForm):
    first_name = forms.CharField(
        label="Nome",
        max_length=150,
        widget=forms.TextInput(attrs={'class': 'form-control', 'required': True})
    )
    last_name = forms.CharField(
        label="Sobrenome",
        max_length=150,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    email = forms.EmailField(
        label="E-mail",
        widget=forms.EmailInput(attrs={'class': 'form-control', 'required': True})
    )
    profile_picture = forms.ImageField(
        label="Foto de Perfil",
        required=False,
        widget=forms.FileInput(attrs={'class': 'form-control-file', 'accept': 'image/*'})
    )

    class Meta:
        model = UserProfile
        fields = ['profile_picture']

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        self.user = user
        super().__init__(*args, **kwargs)
        if user:
            self.fields['first_name'].initial = user.first_name
            self.fields['last_name'].initial = user.last_name
            self.fields['email'].initial = user.email

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if self.user:
            if User.objects.filter(email=email).exclude(pk=self.user.pk).exists():
                raise ValidationError("Este e-mail já está em uso por outro usuário.")
            if User.objects.filter(username=email).exclude(pk=self.user.pk).exists():
                raise ValidationError("Este e-mail/usuário já está em uso.")
        return email
