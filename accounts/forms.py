from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import UserProfile

class UserRegisterForm(UserCreationForm):
    nome = forms.CharField(
        label='Nome Completo',
        max_length=255,
        required=True,
        widget=forms.TextInput(attrs={'placeholder': 'Digite seu nome completo'})
    )
    email = forms.EmailField(
        label='E-mail',
        required=True,
        widget=forms.EmailInput(attrs={'placeholder': 'Digite seu e-mail'})
    )
    cnpj_cpf = forms.CharField(
        label='CNPJ/CPF da Empresa',
        max_length=18,
        required=True,
        widget=forms.TextInput(attrs={'placeholder': 'XX.XXX.XXX/XXXX-XX', 'class': 'cnpj-mask'})
    )
    nome_razao = forms.CharField(
        label='Razão Social / Nome',
        max_length=255,
        required=True,
        widget=forms.TextInput(attrs={'placeholder': 'Digite a razão social ou nome'})
    )

    telefone = forms.CharField(
        label='Telefone',
        max_length=20,
        required=True,
        widget=forms.TextInput(attrs={'placeholder': '(XX) XXXXX-XXXX', 'class': 'telefone-mask'})
    )
    username = forms.CharField(
        label='Nome de Usuário',
        max_length=150,
        required=True,
        widget=forms.TextInput(attrs={'placeholder': 'Digite seu nome de usuário'})
    )
    password1 = forms.CharField(
        label='Senha',
        required=True,
        widget=forms.PasswordInput(attrs={'placeholder': 'Digite sua senha'})
    )
    password2 = forms.CharField(
        label='Confirme a Senha',
        required=True,
        widget=forms.PasswordInput(attrs={'placeholder': 'Confirme sua senha'})
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2', 'nome', 'cnpj_cpf', 'nome_razao', 'telefone']

    def clean_cnpj_cpf(self):
        """Valida o CNPJ/CPF informado no cadastro."""
        from .models import validate_cnpj_cpf
        import re
        
        cnpj_cpf = self.cleaned_data.get('cnpj_cpf')
        if not cnpj_cpf:
            raise forms.ValidationError('CNPJ/CPF é obrigatório.')
        
        # Remove caracteres não numéricos
        digits = re.sub(r"\D", "", cnpj_cpf)
        
        # Valida usando a função do models
        try:
            validate_cnpj_cpf(cnpj_cpf)
        except Exception as e:
            raise forms.ValidationError(str(e))
        
        # Retorna apenas os dígitos para armazenamento consistente
        return digits

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
            # empresa
            from .models import EmpresaContratante, UserProfile
            cnpj_cpf = self.cleaned_data['cnpj_cpf']
            nome_razao = self.cleaned_data['nome_razao']
            empresa, created = EmpresaContratante.objects.get_or_create(
                cnpj_cpf=cnpj_cpf,
                defaults={
                    'nome_razao': nome_razao,
                    'num_usuarios': 1,
                },
            )
            if not empresa.pode_adicionar_usuario():
                raise forms.ValidationError('Limite de usuários desta empresa atingido.')
            perfil = user.profile
            perfil.nome = self.cleaned_data['nome']
            perfil.telefone = self.cleaned_data['telefone']
            perfil.empresa = empresa
            perfil.save()
            empresa.usuarios_cadastrados = empresa.usuarios_ativos
            empresa.save(update_fields=['usuarios_cadastrados'])
        return user

from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core.exceptions import ValidationError

class EmpresaAuthForm(AuthenticationForm):
    """Formulário de login que bloqueia acesso conforme status da empresa."""

    def confirm_login_allowed(self, user):
        # Primeiro chama verificação padrão de super (verifica is_active)
        super().confirm_login_allowed(user)
        UserModel = get_user_model()
        if not hasattr(user, 'profile'):
            raise ValidationError('Usuário sem perfil associado.', code='no_profile')
        empresa = user.profile.empresa
        if not empresa:
            raise ValidationError('Usuário sem empresa vinculada.', code='no_company')

        status = empresa.status
        if status in ('bloqueado', 'expirado', 'vencido', 'suspenso'):
            raise ValidationError('Acesso bloqueado. Entre em contato com o suporte.', code='blocked')
        if status == 'teste' and empresa.vencimento and empresa.vencimento < timezone.now().date():
            raise ValidationError('Período de teste expirado. Entre em contato para contratar o serviço.', code='trial_expired')


class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['nome', 'telefone']
        widgets = {
            'nome': forms.TextInput(attrs={'placeholder': 'Digite seu nome completo'}),
            'telefone': forms.TextInput(attrs={'placeholder': '(XX) XXXXX-XXXX', 'class': 'telefone-mask'}),
        }
