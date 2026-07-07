from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib import messages
from django.contrib.auth.forms import UserCreationForm
from django import forms
from Model.base import Usuario

class RegistroUsuarioForm(UserCreationForm):
    nome = forms.CharField(max_length=255, required=True, label="Nome")
    email = forms.EmailField(required=True, label="E-mail")
    cpf = forms.CharField(max_length=14, required=False, label="CPF")

    class Meta:
        model = Usuario
        fields = ('nome', 'email', 'cpf')

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email:
            email = email.lower()
            if Usuario.objects.filter(username=email).exists() or Usuario.objects.filter(email=email).exists():
                raise forms.ValidationError("Este e-mail já está cadastrado.")
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.first_name = self.cleaned_data.get('nome', '')
        
        email = self.cleaned_data.get('email', '').lower()
        user.email = email
        user.username = email
        user.cpf = self.cleaned_data.get('cpf', '')
        
        # Ensure user is active so there are no restrictions on access
        user.is_active = True
        
        if commit:
            user.save()
        return user

def registro_view(request):
    if request.user.is_authenticated:
        return redirect('home')
        
    if request.method == 'POST':
        form = RegistroUsuarioForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Cadastro realizado com sucesso! Bem-vindo.')
            return redirect('home')
    else:
        form = RegistroUsuarioForm()
    
    from django.contrib.auth.forms import AuthenticationForm
    login_form = AuthenticationForm()
    
    return render(request, 'login.html', {
        'registro_form': form, 
        'form': login_form, 
        'show_register': True
    })
