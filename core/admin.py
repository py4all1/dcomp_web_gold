from django.contrib import admin
from .models import Empresa, NotaFiscalSP, NotaFiscalTomadorSP


@admin.register(Empresa)
class EmpresaAdmin(admin.ModelAdmin):
    list_display = ['cnpj', 'razao_social', 'nome_fantasia', 'inscricao_municipal', 
                    'tem_procurador', 'certificado_validade', 'ativo', 'empresa_contratante']
    list_filter = ['ativo', 'tem_procurador', 'empresa_contratante', 'certificado_validade']
    search_fields = ['cnpj', 'razao_social', 'nome_fantasia', 'inscricao_municipal', 'cpf_cnpj_procurador']
    readonly_fields = ['data_cadastro', 'data_atualizacao', 'certificado_arquivo', 'certificado_validade']
    
    fieldsets = (
        ('Dados Principais', {
            'fields': ('empresa_contratante', 'cnpj', 'razao_social', 'nome_fantasia')
        }),
        ('Inscrições', {
            'fields': ('inscricao_municipal', 'inscricao_estadual')
        }),
        ('Endereço', {
            'fields': ('logradouro', 'numero', 'complemento', 'bairro', 'cidade', 'uf', 'cep'),
            'classes': ('collapse',)
        }),
        ('Contato', {
            'fields': ('telefone', 'email')
        }),
        ('Certificado Digital', {
            'fields': ('senha_certificado', 'certificado_arquivo', 'certificado_validade')
        }),
        ('Procurador', {
            'fields': ('tem_procurador', 'cpf_cnpj_procurador')
        }),
        ('Controle', {
            'fields': ('ativo', 'data_cadastro', 'data_atualizacao')
        }),
    )


@admin.register(NotaFiscalSP)
class NotaFiscalSPAdmin(admin.ModelAdmin):
    list_display = ['id', 'empresa', 'nome_tomador', 'valor_total', 'status_rps', 
                    'data_emissao', 'numero_nfse']
    list_filter = ['status_rps', 'empresa', 'data_emissao', 'iss_retido']
    search_fields = ['nome_tomador', 'cnpj_cpf_tomador', 'numero_nfse', 'descricao']
    readonly_fields = ['data_importacao', 'data_atualizacao', 'data_emissao_nfse']
    date_hierarchy = 'data_emissao'
    
    fieldsets = (
        ('Empresa', {
            'fields': ('empresa',)
        }),
        ('Tomador', {
            'fields': ('cnpj_cpf_tomador', 'nome_tomador', 'email_tomador',
                      'cep_tomador', 'logradouro_tomador', 'numero_tomador',
                      'bairro_tomador', 'cidade_tomador', 'uf_tomador')
        }),
        ('Serviço', {
            'fields': ('cod_servico', 'descricao', 'valor_total', 'deducoes',
                      'aliquota', 'tipo_tributacao')
        }),
        ('Retenções', {
            'fields': ('iss_retido', 'pis_retido', 'cofins_retido',
                      'irrf_retido', 'csll_retido', 'inss_retido')
        }),
        ('Controle', {
            'fields': ('status_rps', 'data_emissao', 'data_importacao', 'data_atualizacao')
        }),
        ('NFS-e', {
            'fields': ('numero_nfse', 'codigo_verificacao', 'data_emissao_nfse',
                      'link_nfse', 'arquivo_pdf'),
            'classes': ('collapse',)
        }),
        ('Observações', {
            'fields': ('observacoes', 'mensagem_erro'),
            'classes': ('collapse',)
        }),
    )


@admin.register(NotaFiscalTomadorSP)
class NotaFiscalTomadorSPAdmin(admin.ModelAdmin):
    list_display = ['id', 'empresa', 'cnpj_cpf_prestador', 'valor_total', 'status_nfts', 
                    'data_prestacao_servico', 'nfts']
    list_filter = ['status_nfts', 'empresa', 'data_prestacao_servico', 'iss_retido', 'regime_tributacao']
    search_fields = ['cnpj_tomador', 'cnpj_cpf_prestador', 'nfts', 'descricao']
    readonly_fields = ['data_importacao', 'data_atualizacao', 'data_emissao_nfts']
    date_hierarchy = 'data_prestacao_servico'
    
    fieldsets = (
        ('Empresa', {
            'fields': ('empresa',)
        }),
        ('Tomador (Declarante)', {
            'fields': ('cnpj_tomador', 'inscricao_municipal', 'data_prestacao_servico')
        }),
        ('Prestador', {
            'fields': ('cnpj_cpf_prestador', 'numero_documento', 'serie',
                      'cidade', 'estado', 'cep')
        }),
        ('Serviço', {
            'fields': ('cod_servico', 'descricao', 'valor_total', 'deducoes',
                      'aliquota', 'tipo_tributacao', 'regime_tributacao', 'tipo_documento')
        }),
        ('Retenção', {
            'fields': ('iss_retido',)
        }),
        ('Controle', {
            'fields': ('status_nfts', 'nfts', 'data_importacao', 'data_atualizacao')
        }),
        ('NFTS', {
            'fields': ('protocolo', 'data_emissao_nfts'),
            'classes': ('collapse',)
        }),
        ('Observações', {
            'fields': ('observacoes', 'mensagem_erro'),
            'classes': ('collapse',)
        }),
    )
