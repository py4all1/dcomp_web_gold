from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import user_passes_test
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Q, Count
from .models import EmpresaContratante, UserProfile
from core.models import Empresa
from datetime import date, timedelta


def is_superuser(user):
    """Verifica se o usuário é superuser"""
    return user.is_superuser


@user_passes_test(is_superuser)
def admin_empresas(request):
    """Tela administrativa para gerenciar empresas contratantes"""
    
    # Filtros
    search = request.GET.get('search', '')
    status_filter = request.GET.get('status', '')
    plano_filter = request.GET.get('plano', '')
    
    # Query base
    empresas = EmpresaContratante.objects.all().annotate(
        total_usuarios=Count('usuarios'),
        total_empresas_emissoras=Count('empresas_emissoras')
    )
    
    # Aplicar filtros
    if search:
        empresas = empresas.filter(
            Q(nome_razao__icontains=search) |
            Q(cnpj_cpf__icontains=search)
        )
    
    if status_filter:
        empresas = empresas.filter(status=status_filter)
    
    if plano_filter:
        empresas = empresas.filter(plano=plano_filter)
    
    # Ordenar
    empresas = empresas.order_by('-id')
    
    # Calcular dias de vencimento para cada empresa
    hoje = date.today()
    empresas_com_dias = []
    for empresa in empresas:
        if empresa.vencimento:
            delta = (empresa.vencimento - hoje).days
            empresa.dias_vencimento = delta
            empresa.dias_vencimento_abs = abs(delta)  # Valor absoluto para exibição
        else:
            empresa.dias_vencimento = None
            empresa.dias_vencimento_abs = None
        empresas_com_dias.append(empresa)
    
    # Estatísticas
    stats = {
        'total': EmpresaContratante.objects.count(),
        'ativas': EmpresaContratante.objects.filter(status='ativo').count(),
        'teste': EmpresaContratante.objects.filter(status='teste').count(),
        'bloqueadas': EmpresaContratante.objects.filter(status='bloqueado').count(),
        'vencidas': EmpresaContratante.objects.filter(status='vencido').count(),
    }
    
    context = {
        'empresas': empresas_com_dias,
        'stats': stats,
        'search': search,
        'status_filter': status_filter,
        'plano_filter': plano_filter,
        'hoje': hoje,
    }
    
    return render(request, 'accounts/admin_empresas.html', context)


@user_passes_test(is_superuser)
def admin_empresa_toggle_status(request, empresa_id):
    """Alterna o status da empresa (ativo/bloqueado)"""
    if request.method == 'POST':
        empresa = get_object_or_404(EmpresaContratante, id=empresa_id)
        
        if empresa.status == 'bloqueado':
            empresa.status = 'ativo'
            messages.success(request, f'Empresa {empresa.nome_razao} foi ATIVADA com sucesso!')
        else:
            empresa.status = 'bloqueado'
            messages.warning(request, f'Empresa {empresa.nome_razao} foi BLOQUEADA!')
        
        empresa.save()
        
        return redirect('accounts:admin_empresas')
    
    return redirect('accounts:admin_empresas')


@user_passes_test(is_superuser)
def admin_empresa_detalhes(request, empresa_id):
    """Detalhes da empresa contratante"""
    empresa = get_object_or_404(EmpresaContratante, id=empresa_id)
    
    # Usuários da empresa
    usuarios = UserProfile.objects.filter(empresa=empresa).select_related('user')
    
    # Empresas emissoras
    empresas_emissoras = Empresa.objects.filter(empresa_contratante=empresa)
    
    # Verificar vencimento
    dias_vencimento = None
    dias_vencimento_abs = None
    if empresa.vencimento:
        delta = empresa.vencimento - date.today()
        dias_vencimento = delta.days
        dias_vencimento_abs = abs(delta.days)
    
    context = {
        'empresa': empresa,
        'usuarios': usuarios,
        'empresas_emissoras': empresas_emissoras,
        'dias_vencimento': dias_vencimento,
        'dias_vencimento_abs': dias_vencimento_abs,
    }
    
    return render(request, 'accounts/admin_empresa_detalhes.html', context)


@user_passes_test(is_superuser)
def admin_empresa_editar(request, empresa_id):
    """Editar empresa contratante"""
    empresa = get_object_or_404(EmpresaContratante, id=empresa_id)
    
    if request.method == 'POST':
        empresa.nome_razao = request.POST.get('nome_razao')
        empresa.cnpj_cpf = request.POST.get('cnpj_cpf')
        empresa.num_usuarios = int(request.POST.get('num_usuarios', 1))
        empresa.num_empresas = int(request.POST.get('num_empresas', 1))
        empresa.status = request.POST.get('status')
        empresa.plano = request.POST.get('plano')
        
        vencimento_str = request.POST.get('vencimento')
        if vencimento_str:
            empresa.vencimento = vencimento_str
        
        empresa.observacoes = request.POST.get('observacoes', '')
        
        empresa.save()
        
        messages.success(request, f'Empresa {empresa.nome_razao} atualizada com sucesso!')
        return redirect('accounts:admin_empresa_detalhes', empresa_id=empresa.id)
    
    return redirect('accounts:admin_empresa_detalhes', empresa_id=empresa.id)


@user_passes_test(is_superuser)
def admin_empresa_renovar(request, empresa_id):
    """Renovar vencimento da empresa"""
    if request.method == 'POST':
        empresa = get_object_or_404(EmpresaContratante, id=empresa_id)
        dias = int(request.POST.get('dias', 30))
        
        if empresa.vencimento and empresa.vencimento > date.today():
            # Se ainda não venceu, adiciona a partir do vencimento atual
            empresa.vencimento = empresa.vencimento + timedelta(days=dias)
        else:
            # Se já venceu, adiciona a partir de hoje
            empresa.vencimento = date.today() + timedelta(days=dias)
        
        empresa.status = 'ativo'
        empresa.save()
        
        messages.success(request, f'Empresa {empresa.nome_razao} renovada por {dias} dias!')
        return redirect('accounts:admin_empresa_detalhes', empresa_id=empresa.id)
    
    return redirect('accounts:admin_empresas')
