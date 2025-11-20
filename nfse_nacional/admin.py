from django.contrib import admin
from .models import NotaFiscalNacional


@admin.register(NotaFiscalNacional)
class NotaFiscalNacionalAdmin(admin.ModelAdmin):
    list_display = ['id', 'empresa', 'nome_tomador', 'valor_total', 'status_nfse', 
                    'data_emissao', 'numero_nfse', 'ibs_devido', 'cbs_devido']
    list_filter = ['status_nfse', 'empresa', 'data_emissao', 'iss_retido', 'ibs_devido', 'cbs_devido']
    search_fields = ['nome_tomador', 'cnpj_cpf_tomador', 'numero_nfse', 'descricao']
    readonly_fields = ['data_importacao', 'data_atualizacao', 'data_emissao_nfse']
    date_hierarchy = 'data_emissao'
    
    fieldsets = (
        ('Empresa', {
            'fields': ('empresa',)
        }),
        ('Tomador', {
            'fields': ('cnpj_cpf_tomador', 'nome_tomador', 'inscricao_municipal_tomador', 'email_tomador')
        }),
        ('Endereço do Tomador', {
            'fields': ('logradouro_tomador', 'numero_tomador', 'complemento_tomador',
                      'bairro_tomador', 'cidade_tomador', 'uf_tomador', 'cep_tomador'),
            'classes': ('collapse',)
        }),
        ('Serviço', {
            'fields': ('data_emissao', 'cod_servico', 'cod_tributacao_municipio', 'descricao',
                      'valor_total', 'deducoes', 'desconto_incondicionado', 'desconto_condicionado')
        }),
        ('Tributação Municipal (ISS)', {
            'fields': ('aliquota_iss', 'tipo_tributacao', 'iss_retido', 'municipio_incidencia')
        }),
        ('Reforma Tributária - IBS', {
            'fields': ('ibs_devido', 'aliquota_ibs', 'valor_ibs', 'ibs_retido'),
            'description': 'Imposto sobre Bens e Serviços (IBS) - Reforma Tributária'
        }),
        ('Reforma Tributária - CBS', {
            'fields': ('cbs_devido', 'aliquota_cbs', 'valor_cbs', 'cbs_retido'),
            'description': 'Contribuição sobre Bens e Serviços (CBS) - Reforma Tributária'
        }),
        ('Retenções Federais', {
            'fields': ('pis_retido', 'cofins_retido', 'irrf_retido', 'csll_retido', 'inss_retido'),
            'classes': ('collapse',)
        }),
        ('RPS', {
            'fields': ('numero_rps', 'serie_rps')
        }),
        ('Controle', {
            'fields': ('status_nfse', 'data_importacao', 'data_atualizacao')
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
