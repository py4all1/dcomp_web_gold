from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.conf import settings
from .models import Empresa
from .forms import EmpresaCadastroForm
import os
from datetime import datetime
from cryptography import x509
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.serialization import pkcs12


@login_required
def home(request):
    """Tela inicial do sistema com informações e apresentação"""
    context = {
        'user': request.user,
        'empresa': request.user.profile.empresa if hasattr(request.user, 'profile') else None,
    }
    return render(request, 'core/home.html', context)


@login_required
def cadastro(request):
    """Tela de cadastro de empresas emissoras"""
    
    # Verifica se o usuário tem empresa contratante vinculada
    if not hasattr(request.user, 'profile') or not request.user.profile.empresa:
        messages.error(request, 'Você precisa estar vinculado a uma empresa contratante para cadastrar empresas emissoras.')
        return redirect('core:home')
    
    empresa_contratante = request.user.profile.empresa
    
    if request.method == 'POST':
        form = EmpresaCadastroForm(request.POST, request.FILES)
        
        if form.is_valid():
            empresa = form.save(commit=False)
            # Vincula à empresa contratante do usuário logado
            empresa.empresa_contratante = empresa_contratante
            
            # Processa o certificado se foi enviado
            certificado_pfx = request.FILES.get('certificado_pfx')
            if certificado_pfx:
                try:
                    # Cria pasta de certificados se não existir
                    cert_dir = os.path.join(settings.BASE_DIR, 'certificados')
                    os.makedirs(cert_dir, exist_ok=True)
                    
                    # Nome do arquivo baseado no CNPJ (ou CNPJ do procurador se preenchido)
                    if empresa.tem_procurador and empresa.cpf_cnpj_procurador:
                        doc_limpo = empresa.cpf_cnpj_procurador.replace('.', '').replace('/', '').replace('-', '')
                    else:
                        doc_limpo = empresa.cnpj.replace('.', '').replace('/', '').replace('-', '')
                    
                    nome_arquivo = f"{doc_limpo}.pfx"
                    caminho_completo = os.path.join(cert_dir, nome_arquivo)
                    
                    # Salva o arquivo
                    with open(caminho_completo, 'wb+') as destination:
                        for chunk in certificado_pfx.chunks():
                            destination.write(chunk)
                    
                    # Extrai a validade do certificado
                    try:
                        senha = empresa.senha_certificado.encode() if empresa.senha_certificado else None
                        with open(caminho_completo, 'rb') as cert_file:
                            p12_data = cert_file.read()
                            # Carrega o certificado PKCS12
                            private_key, certificate, additional_certs = pkcs12.load_key_and_certificates(
                                p12_data, senha, default_backend()
                            )
                            
                            # Extrai a data de validade
                            if certificate:
                                validade = certificate.not_valid_after.date()
                                empresa.certificado_validade = validade
                    except Exception as e:
                        # Erro será tratado no JavaScript
                        pass
                    
                    empresa.certificado_arquivo = nome_arquivo
                    messages.success(request, 'Certificado digital salvo com sucesso!')
                    
                except Exception as e:
                    messages.error(request, f'Erro ao salvar certificado: {str(e)}')
            
            empresa.save()
            messages.success(request, 'Empresa cadastrada com sucesso!')
            return redirect('core:cadastro')
        else:
            messages.error(request, 'Erro ao cadastrar empresa. Verifique os dados.')
    else:
        form = EmpresaCadastroForm()
    
    # Lista apenas as empresas da empresa contratante do usuário
    empresas = Empresa.objects.filter(empresa_contratante=empresa_contratante).order_by('-data_cadastro')
    
    # Datas para verificação de validade
    from datetime import date, timedelta
    today = date.today()
    warning_date = today + timedelta(days=30)  # Alerta 30 dias antes
    
    context = {
        'user': request.user,
        'form': form,
        'empresas': empresas,
        'empresa_contratante': empresa_contratante,
        'today': today,
        'warning_date': warning_date,
    }
    return render(request, 'core/cadastro.html', context)


@login_required
def editar_empresa(request, empresa_id):
    """Edita uma empresa emissora"""
    empresa = get_object_or_404(Empresa, id=empresa_id)
    
    # Verifica se a empresa pertence à empresa contratante do usuário logado
    empresa_contratante = request.user.profile.empresa
    if empresa.empresa_contratante != empresa_contratante:
        messages.error(request, 'Você não tem permissão para editar esta empresa.')
        return redirect('core:cadastro')
    
    if request.method == 'POST':
        form = EmpresaCadastroForm(request.POST, request.FILES, instance=empresa)
        if form.is_valid():
            empresa = form.save(commit=False)
            
            # Processa o certificado se foi enviado um novo
            certificado_pfx = request.FILES.get('certificado_pfx')
            if certificado_pfx:
                try:
                    # Remove certificado antigo se existir
                    if empresa.certificado_arquivo:
                        cert_dir = os.path.join(settings.BASE_DIR, 'certificados')
                        caminho_antigo = os.path.join(cert_dir, empresa.certificado_arquivo)
                        if os.path.exists(caminho_antigo):
                            os.remove(caminho_antigo)
                    
                    # Cria pasta de certificados se não existir
                    cert_dir = os.path.join(settings.BASE_DIR, 'certificados')
                    os.makedirs(cert_dir, exist_ok=True)
                    
                    # Nome do arquivo baseado no CNPJ (ou CNPJ do procurador se preenchido)
                    if empresa.tem_procurador and empresa.cpf_cnpj_procurador:
                        doc_limpo = empresa.cpf_cnpj_procurador.replace('.', '').replace('/', '').replace('-', '')
                    else:
                        doc_limpo = empresa.cnpj.replace('.', '').replace('/', '').replace('-', '')
                    
                    nome_arquivo = f"{doc_limpo}.pfx"
                    caminho_completo = os.path.join(cert_dir, nome_arquivo)
                    
                    # Salva o arquivo
                    with open(caminho_completo, 'wb+') as destination:
                        for chunk in certificado_pfx.chunks():
                            destination.write(chunk)
                    
                    # Extrai a validade do certificado
                    try:
                        senha = empresa.senha_certificado.encode() if empresa.senha_certificado else None
                        with open(caminho_completo, 'rb') as cert_file:
                            p12_data = cert_file.read()
                            # Carrega o certificado PKCS12
                            private_key, certificate, additional_certs = pkcs12.load_key_and_certificates(
                                p12_data, senha, default_backend()
                            )
                            
                            # Extrai a data de validade
                            if certificate:
                                validade = certificate.not_valid_after.date()
                                empresa.certificado_validade = validade
                    except Exception as e:
                        # Erro será tratado no JavaScript
                        pass
                    
                    empresa.certificado_arquivo = nome_arquivo
                    messages.success(request, 'Certificado digital atualizado com sucesso!')
                    
                except Exception as e:
                    messages.error(request, f'Erro ao atualizar certificado: {str(e)}')
            
            empresa.save()
            messages.success(request, 'Empresa atualizada com sucesso!')
            return redirect('core:cadastro')
        else:
            messages.error(request, 'Erro ao atualizar empresa. Verifique os dados.')
    else:
        form = EmpresaCadastroForm(instance=empresa)
    
    context = {
        'user': request.user,
        'form': form,
        'empresa': empresa,
        'editando': True,
    }
    return render(request, 'core/editar_empresa.html', context)


@login_required
def excluir_empresa(request, empresa_id):
    """Exclui uma empresa emissora, seu certificado e todos os dados relacionados"""
    empresa = get_object_or_404(Empresa, id=empresa_id)
    
    # Verifica se a empresa pertence à empresa contratante do usuário logado
    empresa_contratante = request.user.profile.empresa
    if empresa.empresa_contratante != empresa_contratante:
        messages.error(request, 'Você não tem permissão para excluir esta empresa.')
        return redirect('core:cadastro')
    
    nome_empresa = empresa.razao_social
    
    # Contabiliza dados que serão excluídos
    from core.models import NotaFiscalSP, NotaFiscalTomadorSP
    from nfse_nacional.models import NotaFiscalNacional
    
    total_nfs_sp = NotaFiscalSP.objects.filter(empresa=empresa).count()
    total_nfts_sp = NotaFiscalTomadorSP.objects.filter(empresa=empresa).count()
    total_nfse_nacional = NotaFiscalNacional.objects.filter(empresa=empresa).count()
    
    # Remove o certificado se existir
    if empresa.certificado_arquivo:
        try:
            cert_dir = os.path.join(settings.BASE_DIR, 'certificados')
            caminho_completo = os.path.join(cert_dir, empresa.certificado_arquivo)
            if os.path.exists(caminho_completo):
                os.remove(caminho_completo)
        except Exception as e:
            messages.warning(request, f'Erro ao remover certificado: {str(e)}')
    
    # Exclui a empresa (em cascata exclui todas as notas fiscais relacionadas)
    empresa.delete()
    
    # Mensagem de sucesso detalhada
    msg = f'Empresa "{nome_empresa}" excluída com sucesso!'
    if total_nfs_sp > 0 or total_nfts_sp > 0 or total_nfse_nacional > 0:
        msg += f' Foram excluídas também: {total_nfs_sp} NFS-SP, {total_nfts_sp} NFTS-SP e {total_nfse_nacional} NFS-e Nacional.'
    
    messages.success(request, msg)
    return redirect('core:cadastro')


@login_required
def ajuda(request):
    """Tela de ajuda e suporte"""
    context = {
        'user': request.user,
    }
    return render(request, 'core/ajuda.html', context)
