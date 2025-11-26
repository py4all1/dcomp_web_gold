from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
import datetime
import re

PLANOS_CHOICES = (
    ('padrao', 'Padrão'),
    ('pro', 'Pro'),
)

STATUS_CHOICES = (
    ('teste', 'Em Teste'),
    ('ativo', 'Ativo'),
    ('expirado', 'Expirado'),
    ('bloqueado', 'Bloqueado'),
    ('vencido', 'Vencido'),
    ('suspenso', 'Suspenso'),
)

def validate_cnpj_cpf(value: str):
    """Valida CNPJ ou CPF simples (formato apenas dígitos)."""
    digits = re.sub(r"\D", "", value)
    if len(digits) == 11:  # CPF
        if len(set(digits)) == 1:
            raise models.ValidationError("CPF inválido.")
        # validador simples dos dígitos verificadores
        sum1 = sum(int(digits[i]) * (10 - i) for i in range(9))
        dv1 = (sum1 * 10 % 11) % 10
        sum2 = sum(int(digits[i]) * (11 - i) for i in range(10))
        dv2 = (sum2 * 10 % 11) % 10
        if not (dv1 == int(digits[9]) and dv2 == int(digits[10])):
            raise models.ValidationError("CPF inválido.")
    elif len(digits) == 14:  # CNPJ
        if len(set(digits)) == 1:
            raise models.ValidationError("CNPJ inválido.")
        weight1 = [5,4,3,2,9,8,7,6,5,4,3,2]
        weight2 = [6] + weight1
        def calc_dv(nums, weights):
            s = sum(int(n)*w for n,w in zip(nums, weights))
            r = s % 11
            return 0 if r < 2 else 11 - r
        dv1 = calc_dv(digits[:12], weight1)
        dv2 = calc_dv(digits[:13], weight2)
        if not (dv1 == int(digits[12]) and dv2 == int(digits[13])):
            raise models.ValidationError("CNPJ inválido.")
    else:
        raise models.ValidationError("CNPJ/CPF deve ter 11 ou 14 dígitos.")


class EmpresaContratante(models.Model):
    """Empresa que contrata o sistema e agrupa usuários."""
    cnpj_cpf = models.CharField('CNPJ ou CPF', max_length=18, unique=True, validators=[validate_cnpj_cpf])
    nome_razao = models.CharField('Razão Social / Nome', max_length=255)
    usuarios_cadastrados = models.PositiveIntegerField('Usuários Cadastrados', default=1)
    num_usuarios = models.PositiveIntegerField('Limite de Usuários', default=1)
    num_empresas = models.PositiveIntegerField('Limite de Empresas', default=1)  # número máximo de CNPJs/filiais permitidos
    status = models.CharField('Status', max_length=10, choices=STATUS_CHOICES, default='teste')
    plano = models.CharField('Plano', max_length=20, choices=PLANOS_CHOICES, default='padrao')
    vencimento = models.DateField('Vencimento', null=True, blank=True)
    observacoes = models.TextField('Observações', blank=True, null=True)

    class Meta:
        verbose_name = 'Empresa Contratante'
        verbose_name_plural = 'Empresas Contratantes'

    def __str__(self):
        return f"{self.nome_razao} ({self.cnpj_cpf})"

    @property
    def usuarios_ativos(self):
        return self.usuarios.count()

    def pode_adicionar_usuario(self):
        return self.usuarios_ativos < self.num_usuarios

    def save(self, *args, **kwargs):
        if not self.vencimento:
            self.vencimento = timezone.now().date() + datetime.timedelta(days=7)
        super().save(*args, **kwargs)


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    empresa = models.ForeignKey(EmpresaContratante, on_delete=models.SET_NULL, related_name='usuarios', null=True, blank=True)
    nome = models.CharField('Nome Completo', max_length=255)
    # cnpj_empresa removido - usar empresa.cnpj_cpf
    # nome_empresa removido - usar empresa.nome_razao
    telefone = models.CharField('Telefone', max_length=20)
    # status armazenado na empresa
    data_cadastro = models.DateTimeField('Data de Cadastro', auto_now_add=True)
    # data_expiracao armazenada na empresa
    
    class Meta:
        verbose_name = 'Perfil de Usuário'
        verbose_name_plural = 'Perfis de Usuários'
    
    def __str__(self):
        return self.user.username
    
    def save(self, *args, **kwargs):
        # criação automática mantém empresa nula; será definida no fluxo de registrosuários da empresa
        if self.empresa and not self.empresa.pode_adicionar_usuario() and not self.pk:
            raise ValueError("Limite de usuários desta empresa atingido.")
        super().save(*args, **kwargs)
    
    @property
    def dias_restantes(self):
        """Retorna o número de dias restantes do período de teste"""
        if self.empresa.status != 'teste':
            return 0
        
        if not self.empresa.vencimento:
            return 0
            
        delta = datetime.datetime.combine(self.empresa.vencimento, datetime.time.min, tzinfo=timezone.utc) - timezone.now()
        dias = delta.days
        
        if dias <= 0:
            # Atualiza o status para expirado se o prazo acabou
            self.empresa.status = 'expirado'
            self.empresa.save(update_fields=['status'])
            return 0
            
        return dias

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Cria um perfil de usuário quando um novo usuário é criado"""
    if created:
        UserProfile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """Salva o perfil de usuário quando o usuário é salvo"""
    try:
        instance.profile.save()
    except UserProfile.DoesNotExist:
        UserProfile.objects.create(user=instance)
