from django.db import models
from accounts.models import EmpresaContratante
from django.utils import timezone
import re


def validate_cnpj(value: str):
    """Valida CNPJ (formato apenas dígitos)."""
    digits = re.sub(r"\D", "", value)
    if len(digits) != 14:
        raise models.ValidationError("CNPJ deve ter 14 dígitos.")
    
    if len(set(digits)) == 1:
        raise models.ValidationError("CNPJ inválido.")
    
    weight1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    weight2 = [6] + weight1
    
    def calc_dv(nums, weights):
        s = sum(int(n) * w for n, w in zip(nums, weights))
        r = s % 11
        return 0 if r < 2 else 11 - r
    
    dv1 = calc_dv(digits[:12], weight1)
    dv2 = calc_dv(digits[:13], weight2)
    
    if not (dv1 == int(digits[12]) and dv2 == int(digits[13])):
        raise models.ValidationError("CNPJ inválido.")


class Empresa(models.Model):
    """Empresa emissora de notas fiscais"""
    
    empresa_contratante = models.ForeignKey(
        EmpresaContratante,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='empresas_emissoras',
        verbose_name='Empresa Contratante',
        help_text='Empresa que contratou o sistema'
    )
    
    cnpj = models.CharField(
        'CNPJ',
        max_length=18,
        unique=True,
        validators=[validate_cnpj],
        help_text='CNPJ da empresa emissora'
    )
    
    razao_social = models.CharField(
        'Razão Social',
        max_length=255
    )
    
    nome_fantasia = models.CharField(
        'Nome Fantasia',
        max_length=255,
        blank=True,
        null=True
    )
    
    inscricao_municipal = models.CharField(
        'Inscrição Municipal',
        max_length=50,
        blank=True,
        null=True
    )
    
    inscricao_estadual = models.CharField(
        'Inscrição Estadual',
        max_length=50,
        blank=True,
        null=True
    )
    
    # Endereço
    logradouro = models.CharField('Logradouro', max_length=255, blank=True, null=True)
    numero = models.CharField('Número', max_length=20, blank=True, null=True)
    complemento = models.CharField('Complemento', max_length=100, blank=True, null=True)
    bairro = models.CharField('Bairro', max_length=100, blank=True, null=True)
    cidade = models.CharField('Cidade', max_length=100, blank=True, null=True)
    uf = models.CharField('UF', max_length=2, blank=True, null=True)
    cep = models.CharField('CEP', max_length=10, blank=True, null=True)
    
    # Contato
    telefone = models.CharField('Telefone', max_length=20, blank=True, null=True)
    email = models.EmailField('E-mail', blank=True, null=True)
    
    # Certificado Digital
    senha_certificado = models.CharField(
        'Senha do Certificado',
        max_length=255,
        blank=True,
        null=True,
        help_text='Senha do certificado digital A1'
    )
    
    certificado_arquivo = models.CharField(
        'Nome do Arquivo do Certificado',
        max_length=255,
        blank=True,
        null=True
    )
    
    certificado_validade = models.DateField(
        'Validade do Certificado',
        null=True,
        blank=True
    )
    
    # Procurador
    tem_procurador = models.BooleanField(
        'Possui Procurador',
        default=False,
        help_text='Marque se a empresa possui procurador'
    )
    
    cpf_cnpj_procurador = models.CharField(
        'CPF/CNPJ do Procurador',
        max_length=18,
        blank=True,
        null=True,
        help_text='CPF ou CNPJ do procurador'
    )
    
    # Controle
    ativo = models.BooleanField('Ativo', default=True)
    data_cadastro = models.DateTimeField('Data de Cadastro', auto_now_add=True)
    data_atualizacao = models.DateTimeField('Última Atualização', auto_now=True)
    
    class Meta:
        verbose_name = 'Empresa Emissora'
        verbose_name_plural = 'Empresas Emissoras'
        ordering = ['-data_cadastro']
    
    def __str__(self):
        return f"{self.razao_social} ({self.cnpj})"
    
    @property
    def cnpj_formatado(self):
        """Retorna CNPJ formatado"""
        cnpj = re.sub(r'\D', '', self.cnpj)
        if len(cnpj) == 14:
            return f"{cnpj[:2]}.{cnpj[2:5]}.{cnpj[5:8]}/{cnpj[8:12]}-{cnpj[12:]}"
        return self.cnpj
    
    @property
    def certificado_vencido(self):
        """Verifica se o certificado está vencido"""
        if not self.certificado_validade:
            return None
        from datetime import date
        return self.certificado_validade < date.today()
    
    @property
    def certificado_proximo_vencimento(self):
        """Verifica se o certificado está próximo do vencimento (30 dias)"""
        if not self.certificado_validade:
            return None
        from datetime import date, timedelta
        return self.certificado_validade < (date.today() + timedelta(days=30))


STATUS_RPS_CHOICES = (
    ('pendente', 'Pendente'),
    ('emitida', 'Emitida'),
    ('cancelada', 'Cancelada'),
    ('erro', 'Erro'),
)

TIPO_TRIBUTACAO_CHOICES = (
    ('T', 'Tributado no Município'),
    ('F', 'Tributado Fora do Município'),
    ('I', 'Isento'),
    ('N', 'Não Tributado'),
)


class NotaFiscalSP(models.Model):
    """Nota Fiscal de Serviço - São Paulo"""
    
    empresa = models.ForeignKey(
        Empresa,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='notas_fiscais',
        verbose_name='Empresa Prestadora'
    )
    
    # CNPJ do Contribuinte (Empresa Prestadora)
    cnpj_contribuinte = models.CharField('CNPJ Contribuinte', max_length=18, blank=True, null=True)
    
    # Dados do Tomador
    cnpj_cpf_tomador = models.CharField('CNPJ/CPF Tomador', max_length=18, blank=True, null=True)
    nome_tomador = models.CharField('Nome/Razão Social Tomador', max_length=255)
    cep_tomador = models.CharField('CEP', max_length=10, blank=True, null=True)
    logradouro_tomador = models.CharField('Logradouro', max_length=255, blank=True, null=True)
    numero_tomador = models.CharField('Número', max_length=20, blank=True, null=True)
    bairro_tomador = models.CharField('Bairro', max_length=100, blank=True, null=True)
    cidade_tomador = models.CharField('Cidade', max_length=100, blank=True, null=True)
    uf_tomador = models.CharField('UF', max_length=2, blank=True, null=True)
    email_tomador = models.EmailField('E-mail', blank=True, null=True)
    
    # Dados do Serviço
    cod_servico = models.CharField('Código do Serviço', max_length=10)
    descricao = models.TextField('Descrição do Serviço')
    valor_total = models.DecimalField('Valor Total', max_digits=15, decimal_places=2)
    deducoes = models.DecimalField('Deduções', max_digits=15, decimal_places=2, default=0)
    aliquota = models.DecimalField('Alíquota (%)', max_digits=5, decimal_places=2)
    tipo_tributacao = models.CharField('Tipo de Tributação', max_length=1, choices=TIPO_TRIBUTACAO_CHOICES)
    
    # Retenções
    iss_retido = models.BooleanField('ISS Retido', default=False)
    pis_retido = models.DecimalField('PIS Retido', max_digits=15, decimal_places=2, default=0)
    cofins_retido = models.DecimalField('COFINS Retido', max_digits=15, decimal_places=2, default=0)
    irrf_retido = models.DecimalField('IRRF Retido', max_digits=15, decimal_places=2, default=0)
    csll_retido = models.DecimalField('CSLL Retido', max_digits=15, decimal_places=2, default=0)
    inss_retido = models.DecimalField('INSS Retido', max_digits=15, decimal_places=2, default=0)
    
    # Dados do RPS
    numero_rps = models.CharField('Número RPS', max_length=15, blank=True, null=True)
    serie_rps = models.CharField('Série RPS', max_length=5, default='RPS', blank=True)
    tributacao_rps = models.CharField('Tributação RPS', max_length=1, choices=TIPO_TRIBUTACAO_CHOICES, blank=True, null=True)
    
    # Controle
    status_rps = models.CharField('Status', max_length=20, choices=STATUS_RPS_CHOICES, default='pendente')
    data_emissao = models.DateField('Data de Emissão', null=True, blank=True)
    data_importacao = models.DateTimeField('Data de Importação', auto_now_add=True)
    data_atualizacao = models.DateTimeField('Última Atualização', auto_now=True)
    
    # Dados da NFS-e (após emissão)
    numero_nfse = models.CharField('Número NFS-e', max_length=50, blank=True, null=True)
    codigo_verificacao = models.CharField('Código de Verificação', max_length=100, blank=True, null=True)
    data_emissao_nfse = models.DateTimeField('Data/Hora Emissão NFS-e', null=True, blank=True)
    link_nfse = models.URLField('Link NFS-e', blank=True, null=True)
    arquivo_pdf = models.CharField('Arquivo PDF', max_length=255, blank=True, null=True)
    
    # Observações e Erros
    observacoes = models.TextField('Observações', blank=True, null=True)
    mensagem_erro = models.TextField('Mensagem de Erro', blank=True, null=True)
    
    class Meta:
        verbose_name = 'Nota Fiscal SP'
        verbose_name_plural = 'Notas Fiscais SP'
        ordering = ['-data_importacao']
        indexes = [
            models.Index(fields=['empresa', 'status_rps']),
            models.Index(fields=['data_emissao']),
            models.Index(fields=['numero_nfse']),
        ]
    
    def __str__(self):
        if self.numero_nfse:
            return f"NFS-e {self.numero_nfse} - {self.nome_tomador}"
        return f"RPS {self.id} - {self.nome_tomador}"
    
    @property
    def valor_iss(self):
        """Calcula o valor do ISS"""
        base_calculo = self.valor_total - self.deducoes
        return (base_calculo * self.aliquota) / 100
    
    @property
    def valor_liquido(self):
        """Calcula o valor líquido"""
        total_retencoes = (
            self.pis_retido + self.cofins_retido + 
            self.irrf_retido + self.csll_retido + self.inss_retido
        )
        if self.iss_retido:
            total_retencoes += self.valor_iss
        return self.valor_total - total_retencoes


STATUS_NFTS_CHOICES = (
    ('pendente', 'Pendente'),
    ('emitida', 'Emitida'),
    ('cancelada', 'Cancelada'),
    ('erro', 'Erro'),
)

REGIME_TRIBUTACAO_CHOICES = (
    ('simples', 'Simples Nacional'),
    ('presumido', 'Lucro Presumido'),
    ('real', 'Lucro Real'),
    ('mei', 'MEI'),
)

TIPO_DOCUMENTO_CHOICES = (
    ('nfe', 'NF-e'),
    ('nfse', 'NFS-e'),
    ('cupom', 'Cupom Fiscal'),
    ('recibo', 'Recibo'),
)


class NotaFiscalTomadorSP(models.Model):
    """Nota Fiscal do Tomador - São Paulo (NFTS)"""
    
    empresa = models.ForeignKey(
        Empresa,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='notas_tomador',
        verbose_name='Empresa Tomadora'
    )
    
    # CNPJ do Contribuinte (Empresa Tomadora)
    cnpj_contribuinte = models.CharField('CNPJ Contribuinte', max_length=18, blank=True, null=True)
    
    # Dados do Tomador (Empresa que está declarando)
    cnpj_tomador = models.CharField('CNPJ Tomador', max_length=18)
    inscricao_municipal = models.CharField('Inscrição Municipal', max_length=50)
    data_prestacao_servico = models.DateField('Data de Prestação do Serviço')
    
    # Dados do Prestador (Quem prestou o serviço)
    cnpj_cpf_prestador = models.CharField('CNPJ/CPF Prestador', max_length=18)
    numero_documento = models.CharField('Número do Documento', max_length=50, blank=True, null=True)
    serie = models.CharField('Série', max_length=10, blank=True, null=True)
    
    # Localização do Prestador
    cidade = models.CharField('Cidade', max_length=100, blank=True, null=True)
    estado = models.CharField('Estado', max_length=2, blank=True, null=True)
    cep = models.CharField('CEP', max_length=10, blank=True, null=True)
    
    # Dados do Serviço
    cod_servico = models.CharField('Código do Serviço', max_length=10)
    descricao = models.TextField('Descrição do Serviço')
    valor_total = models.DecimalField('Valor Total', max_digits=15, decimal_places=2)
    deducoes = models.DecimalField('Deduções', max_digits=15, decimal_places=2, default=0)
    aliquota = models.DecimalField('Alíquota (%)', max_digits=5, decimal_places=2)
    tipo_tributacao = models.CharField('Tipo de Tributação', max_length=1, choices=TIPO_TRIBUTACAO_CHOICES)
    regime_tributacao = models.CharField('Regime de Tributação', max_length=20, choices=REGIME_TRIBUTACAO_CHOICES)
    tipo_documento = models.CharField('Tipo de Documento', max_length=20, choices=TIPO_DOCUMENTO_CHOICES)
    
    # Retenção
    iss_retido = models.BooleanField('ISS Retido', default=False)
    
    # Controle
    nfts = models.CharField('Número NFTS', max_length=50, blank=True, null=True)
    status_nfts = models.CharField('Status', max_length=20, choices=STATUS_NFTS_CHOICES, default='pendente')
    data_importacao = models.DateTimeField('Data de Importação', auto_now_add=True)
    data_atualizacao = models.DateTimeField('Última Atualização', auto_now=True)
    
    # Dados da NFTS (após emissão)
    protocolo = models.CharField('Protocolo', max_length=100, blank=True, null=True)
    data_emissao_nfts = models.DateTimeField('Data/Hora Emissão NFTS', null=True, blank=True)
    
    # Observações e Erros
    observacoes = models.TextField('Observações', blank=True, null=True)
    mensagem_erro = models.TextField('Mensagem de Erro', blank=True, null=True)
    
    class Meta:
        verbose_name = 'Nota Fiscal Tomador SP'
        verbose_name_plural = 'Notas Fiscais Tomador SP'
        ordering = ['-data_importacao']
        indexes = [
            models.Index(fields=['empresa', 'status_nfts']),
            models.Index(fields=['data_prestacao_servico']),
            models.Index(fields=['nfts']),
        ]
    
    def __str__(self):
        if self.nfts:
            return f"NFTS {self.nfts} - {self.cnpj_cpf_prestador}"
        return f"NFTS {self.id} - {self.cnpj_cpf_prestador}"
    
    @property
    def valor_iss(self):
        """Calcula o valor do ISS"""
        base_calculo = self.valor_total - self.deducoes
        return (base_calculo * self.aliquota) / 100
