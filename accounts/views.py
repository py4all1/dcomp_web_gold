from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import views as auth_views
from django.urls import reverse_lazy
from django.views.generic import CreateView
from django.contrib.auth.models import User
from .forms import UserRegisterForm, UserProfileForm
from .models import UserProfile

from django import forms
import logging
# from email_ import send_email  # Descomente quando configurar o módulo de email

def register(request):
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            try:
                user = form.save()
                # Envia e-mail de boas-vindas (não bloqueante do fluxo)
                # Descomente quando configurar o módulo de email
                # try:
                #     nome = form.cleaned_data.get('nome') or getattr(user, 'username', 'Usuário')
                #     destinatario = form.cleaned_data.get('email') or getattr(user, 'email', None)
                #     if destinatario:
                #         send_email(destinatarios=[destinatario], nome=nome, assunto="Bem-vindo ao Emissor Gold", cc=["contato@emissorgold.com.br"])
                # except Exception as mail_err:
                #     logger = logging.getLogger(__name__)
                #     logger.error(f"Falha ao enviar e-mail de boas-vindas: {mail_err}")
                messages.success(request, 'Conta criada com sucesso! Você pode fazer login agora.')
                return redirect('login')
            except forms.ValidationError as e:
                form.add_error(None, e.message)
    else:
        form = UserRegisterForm()
    
    return render(request, 'registration/register.html', {'form': form})

# Usando função ao invés de classe para melhor controle do formulário
RegisterView = register

from django.contrib.auth import logout

def logout_view(request):
    """Encerra a sessão e redireciona para a tela de login."""
    logout(request)
    return redirect('accounts:login')


def profile(request):
    if request.method == 'POST':
        form = UserProfileForm(request.POST, instance=request.user.profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Seu perfil foi atualizado com sucesso!')
            return redirect('accounts:profile')
    else:
        form = UserProfileForm(instance=request.user.profile)
    
    context = {
        'form': form,
        'user': request.user,
    }
    return render(request, 'accounts/profile.html', context)
