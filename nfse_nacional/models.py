from django.db import models
from core.models import Empresa, TIPO_TRIBUTACAO_CHOICES
from django.utils import timezone


STATUS_NFSE_CHOICES = (
    ('pendente', 'Pendente'),
    ('emitida', 'Emitida'),
    ('cancelada', 'Cancelada'),
    ('erro', 'Erro'),
)


class NotaFiscalNacional(models.Model):
    """Nota Fiscal de Serviço Eletrônica Nacional (com Reforma Tributária)"""
    
    empresa = models.ForeignKey(
        Empresa,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='notas_nacionais',
        verbose_name='Empresa Emissora'
    )
    cnpj_contribuinte = models.CharField('CNPJ Contribuinte', max_length=18, help_text='CNPJ da empresa emissora')
    
    # Dados do Tomador
    cnpj_cpf_tomador = models.CharField('CNPJ/CPF Tomador', max_length=18)
    nome_tomador = models.CharField('Nome/Razão Social', max_length=200)
    inscricao_municipal_tomador = models.CharField('Inscrição Municipal', max_length=50, blank=True, null=True)
    
    # Endereço do Tomador
    logradouro_tomador = models.CharField('Logradouro', max_length=200, blank=True, null=True)
    numero_tomador = models.CharField('Número', max_length=20, blank=True, null=True)
    complemento_tomador = models.CharField('Complemento', max_length=100, blank=True, null=True)
    bairro_tomador = models.CharField('Bairro', max_length=100, blank=True, null=True)
    cidade_tomador = models.CharField('Cidade', max_length=100, blank=True, null=True)
    uf_tomador = models.CharField('UF', max_length=2, blank=True, null=True)
    cep_tomador = models.CharField('CEP', max_length=10, blank=True, null=True)
    email_tomador = models.EmailField('E-mail', blank=True, null=True)
    
    # Dados do Serviço
    data_emissao = models.DateField('Data de Emissão', default=timezone.now)
    cod_servico = models.CharField('Código do Serviço', max_length=10)
    cod_tributacao_municipio = models.CharField('Código Tributação Município', max_length=20, blank=True, null=True)
    descricao = models.TextField('Descrição do Serviço')
    valor_total = models.DecimalField('Valor Total', max_digits=15, decimal_places=2)
    deducoes = models.DecimalField('Deduções', max_digits=15, decimal_places=2, default=0)
    desconto_incondicionado = models.DecimalField('Desconto Incondicionado', max_digits=15, decimal_places=2, default=0)
    desconto_condicionado = models.DecimalField('Desconto Condicionado', max_digits=15, decimal_places=2, default=0)
    
    # Tributação Municipal (ISS)
    aliquota_iss = models.DecimalField('Alíquota ISS (%)', max_digits=5, decimal_places=2)
    tipo_tributacao = models.CharField('Tipo de Tributação', max_length=1, choices=TIPO_TRIBUTACAO_CHOICES)
    iss_retido = models.BooleanField('ISS Retido', default=False)
    municipio_incidencia = models.CharField('Município de Incidência', max_length=100, blank=True, null=True)
    
    # REFORMA TRIBUTÁRIA - IBS (Imposto sobre Bens e Serviços)
    ibs_devido = models.BooleanField('IBS Devido', default=True, help_text='Imposto sobre Bens e Serviços (Reforma Tributária)')
    aliquota_ibs = models.DecimalField('Alíquota IBS (%)', max_digits=5, decimal_places=2, default=0, 
                                       help_text='Alíquota do IBS conforme Reforma Tributária')
    valor_ibs = models.DecimalField('Valor IBS', max_digits=15, decimal_places=2, default=0)
    ibs_retido = models.BooleanField('IBS Retido na Fonte', default=False)
    
    # REFORMA TRIBUTÁRIA - CBS (Contribuição sobre Bens e Serviços)
    cbs_devido = models.BooleanField('CBS Devido', default=True, help_text='Contribuição sobre Bens e Serviços (Reforma Tributária)')
    aliquota_cbs = models.DecimalField('Alíquota CBS (%)', max_digits=5, decimal_places=2, default=0,
                                       help_text='Alíquota da CBS conforme Reforma Tributária')
    valor_cbs = models.DecimalField('Valor CBS', max_digits=15, decimal_places=2, default=0)
    cbs_retido = models.BooleanField('CBS Retido na Fonte', default=False)
    
    # Retenções Federais (mantidas durante transição)
    pis_retido = models.DecimalField('PIS Retido', max_digits=15, decimal_places=2, default=0)
    cofins_retido = models.DecimalField('COFINS Retido', max_digits=15, decimal_places=2, default=0)
    irrf_retido = models.DecimalField('IRRF Retido', max_digits=15, decimal_places=2, default=0)
    csll_retido = models.DecimalField('CSLL Retido', max_digits=15, decimal_places=2, default=0)
    inss_retido = models.DecimalField('INSS Retido', max_digits=15, decimal_places=2, default=0)
    
    # Informações Complementares
    numero_rps = models.CharField('Número RPS', max_length=50, blank=True, null=True)
    serie_rps = models.CharField('Série RPS', max_length=10, blank=True, null=True)
    observacoes = models.TextField('Observações', blank=True, null=True)
    
    # Controle
    status_nfse = models.CharField('Status', max_length=20, choices=STATUS_NFSE_CHOICES, default='pendente')
    data_importacao = models.DateTimeField('Data de Importação', auto_now_add=True)
    data_atualizacao = models.DateTimeField('Última Atualização', auto_now=True)
    
    # Dados da NFS-e (após emissão)
    numero_nfse = models.CharField('Número NFS-e', max_length=50, blank=True, null=True)
    codigo_verificacao = models.CharField('Código de Verificação', max_length=100, blank=True, null=True)
    data_emissao_nfse = models.DateTimeField('Data/Hora Emissão NFS-e', null=True, blank=True)
    link_nfse = models.URLField('Link NFS-e', blank=True, null=True)
    arquivo_pdf = models.CharField('Arquivo PDF', max_length=255, blank=True, null=True)
    
    # Erros
    mensagem_erro = models.TextField('Mensagem de Erro', blank=True, null=True)
    
    class Meta:
        verbose_name = 'Nota Fiscal Nacional'
        verbose_name_plural = 'Notas Fiscais Nacionais'
        ordering = ['-data_importacao']
        indexes = [
            models.Index(fields=['empresa', 'status_nfse']),
            models.Index(fields=['cnpj_contribuinte']),
            models.Index(fields=['data_emissao']),
            models.Index(fields=['numero_nfse']),
        ]
    
    def __str__(self):
        if self.numero_nfse:
            return f"NFS-e {self.numero_nfse} - {self.nome_tomador}"
        return f"RPS {self.numero_rps or self.id} - {self.nome_tomador}"
    
    @property
    def valor_iss(self):
        """Calcula o valor do ISS"""
        base_calculo = self.valor_total - self.deducoes - self.desconto_incondicionado
        return (base_calculo * self.aliquota_iss) / 100
    
    @property
    def valor_liquido(self):
        """Calcula o valor líquido (considerando reforma tributária)"""
        total_retencoes = (
            self.pis_retido + self.cofins_retido + 
            self.irrf_retido + self.csll_retido + self.inss_retido
        )
        
        # Adiciona IBS e CBS se retidos
        if self.ibs_retido:
            total_retencoes += self.valor_ibs
        if self.cbs_retido:
            total_retencoes += self.valor_cbs
        
        # Adiciona ISS se retido
        if self.iss_retido:
            total_retencoes += self.valor_iss
        
        return self.valor_total - total_retencoes
