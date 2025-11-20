from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User

from .models import EmpresaContratante, UserProfile


class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Perfil'
    fk_name = 'user'


@admin.register(EmpresaContratante)
class EmpresaContratanteAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'nome_razao',
        'cnpj_cpf',
        'status',
        'plano',
        'usuarios_ativos',
        'num_usuarios',
        'num_empresas',
        'vencimento',
    )
    list_filter = ('status', 'plano')
    search_fields = ('nome_razao', 'cnpj_cpf')
    ordering = ('nome_razao',)


class CustomUserAdmin(BaseUserAdmin):
    inlines = (UserProfileInline,)

    list_display = BaseUserAdmin.list_display + (
        'get_empresa',
        'get_status',
    )

    def get_empresa(self, obj):
        return obj.profile.empresa.nome_razao if obj.profile.empresa else '-'

    get_empresa.short_description = 'Empresa'
    get_empresa.admin_order_field = 'profile__empresa__nome_razao'

    def get_status(self, obj):
        if obj.profile.empresa:
            return obj.profile.empresa.status
        return '-'

    get_status.short_description = 'Status Empresa'
    get_status.admin_order_field = 'profile__empresa__status'


# Unregister original User and register with custom admin
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)

# Register your models here.
