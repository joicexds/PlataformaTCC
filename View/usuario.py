from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.forms import UserCreationForm, SetPasswordForm
from django import forms
from Model.base import Usuario

class UsuarioForm(UserCreationForm):
    nome = forms.CharField(max_length=255, required=True, label="Nome")
    email = forms.EmailField(required=True, label="E-mail")
    cpf = forms.CharField(max_length=14, required=True, label="CPF")

    class Meta:
        model = Usuario
        fields = ('nome', 'email', 'cpf')

    def clean_cpf(self):
        cpf = self.cleaned_data.get('cpf', '')
        cpf = ''.join(filter(str.isdigit, cpf))
        if len(cpf) != 11:
            raise forms.ValidationError("O CPF deve conter exatamente 11 números.")
        return cpf

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email:
            email = email.lower()
            if Usuario.objects.filter(username=email).exclude(pk=self.instance.pk).exists() or \
               Usuario.objects.filter(email=email).exclude(pk=self.instance.pk).exists():
                raise forms.ValidationError("Este e-mail já está cadastrado.")
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.first_name = self.cleaned_data.get('nome', '')
        
        email = self.cleaned_data.get('email', '').lower()
        user.email = email
        user.username = email
        user.cpf = self.cleaned_data.get('cpf', '')
        
        user.is_active = True
        
        if commit:
            user.save()
        return user

class UsuarioUpdateForm(forms.ModelForm):
    nome = forms.CharField(max_length=255, required=True, label="Nome")
    email = forms.EmailField(required=True, label="E-mail")
    cpf = forms.CharField(max_length=14, required=True, label="CPF")

    class Meta:
        model = Usuario
        fields = ('nome', 'email', 'cpf')

    def clean_cpf(self):
        cpf = self.cleaned_data.get('cpf', '')
        cpf = ''.join(filter(str.isdigit, cpf))
        if len(cpf) != 11:
            raise forms.ValidationError("O CPF deve conter exatamente 11 números.")
        return cpf

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email:
            email = email.lower()
            if Usuario.objects.filter(username=email).exclude(pk=self.instance.pk).exists() or \
               Usuario.objects.filter(email=email).exclude(pk=self.instance.pk).exists():
                raise forms.ValidationError("Este e-mail já está cadastrado.")
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.first_name = self.cleaned_data.get('nome', '')
        email = self.cleaned_data.get('email', '').lower()
        user.email = email
        user.username = email
        user.cpf = self.cleaned_data.get('cpf', '')
        if commit:
            user.save()
        return user

@login_required
def usuario_lista(request):
    usuarios = Usuario.objects.all().order_first_name() if hasattr(Usuario.objects.all(), 'order_first_name') else Usuario.objects.all().order_by('first_name')
    return render(request, 'usuario_lista.html', {
        'usuarios': usuarios,
        'active_menu': 'usuarios'
    })

@login_required
def usuario_form(request, id_usuario=None):
    if id_usuario:
        usuario = get_object_or_404(Usuario, pk=id_usuario)
        if request.method == 'POST':
            form = UsuarioUpdateForm(request.POST, instance=usuario)
            if form.is_valid():
                form.save()
                messages.success(request, 'Usuário atualizado com sucesso!')
                return redirect('usuario_lista')
        else:
            form = UsuarioUpdateForm(instance=usuario, initial={'nome': usuario.first_name})
    else:
        usuario = None
        if request.method == 'POST':
            form = UsuarioForm(request.POST)
            if form.is_valid():
                form.save()
                messages.success(request, 'Usuário cadastrado com sucesso!')
                return redirect('usuario_lista')
        else:
            form = UsuarioForm()

    return render(request, 'usuario_form.html', {
        'form': form,
        'usuario': usuario,
        'active_menu': 'usuarios'
    })

@login_required
def usuario_mudar_senha(request, id_usuario):
    usuario = get_object_or_404(Usuario, pk=id_usuario)
    
    if request.method == 'POST':
        form = SetPasswordForm(usuario, request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Senha do usuário atualizada com sucesso!')
            return redirect('usuario_lista')
    else:
        form = SetPasswordForm(usuario)

    return render(request, 'usuario_form.html', {
        'form': form,
        'usuario': usuario,
        'is_password_change': True,
        'active_menu': 'usuarios'
    })

@login_required
def usuario_excluir(request, id_usuario):
    usuario = get_object_or_404(Usuario, pk=id_usuario)
    if request.method == 'POST':
        usuario.delete()
        messages.success(request, 'Usuário excluído com sucesso!')
    return redirect('usuario_lista')
