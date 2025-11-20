"""
Serviço de Eventos NFS-e para Django
Adaptado para funcionar com Django ORM e estrutura web
"""
import xml.etree.ElementTree as ET
import lxml.etree as etree
from datetime import datetime
import locale
import os
from django.conf import settings

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.serialization import load_pem_private_key
from cryptography.hazmat.backends import default_backend
import base64

# Configurar locale para formatação de valores
try:
    locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')
except:
    try:
        locale.setlocale(locale.LC_ALL, '')
    except:
        pass


class EventoNFeDjango:
    """
    Classe para criar XMLs de eventos da NFS-e São Paulo
    Adaptada para Django
    """
    
    def __init__(self, empresa):
        """
        Inicializa o evento com uma empresa Django
        
        Args:
            empresa: Instância do modelo Empresa do Django
        """
        self.empresa = empresa
        self.cnpj = empresa.cnpj.replace('.', '').replace('/', '').replace('-', '')
        self.inscricao_municipal = empresa.inscricao_municipal
        
    def get_certificado_pem_path(self):
        """Retorna o caminho do certificado PEM"""
        cert_dir = os.path.join(settings.BASE_DIR, 'certificados')
        os.makedirs(cert_dir, exist_ok=True)
        pem_path = os.path.join(cert_dir, f"{self.cnpj}.pem")
        
        if not os.path.exists(pem_path):
            # Se não existe PEM, precisa converter do PFX
            from .certificado_service import CertificadoService
            cert_service = CertificadoService()
            cert_service.converter_pfx_para_pem(self.empresa)
            
        return pem_path
    
    def formata_valor(self, valor):
        """Formata valor monetário"""
        if not valor or valor == 0:
            return '0'
        try:
            retorno = str(locale.currency(float(valor), grouping=False, symbol=False))
            return retorno
        except:
            return str(valor) if valor else '0'
    
    def criar_assinatura_rps(self, dados, cancelamento=False):
        """
        Cria assinatura digital do RPS
        
        Args:
            dados: Lista com dados do RPS
            cancelamento: Se True, cria assinatura para cancelamento
        """
        if cancelamento:
            cadeia_caracteres = self.string_nfe_cancelamento(dados)
        else:
            cadeia_caracteres = self.string_nfe(dados)
        
        caminho_pem = self.get_certificado_pem_path()
        
        with open(caminho_pem, 'rb') as key_file:
            private_key = serialization.load_pem_private_key(
                key_file.read(),
                password=None,
                backend=default_backend()
            )
        
        assinatura = private_key.sign(
            cadeia_caracteres.encode('utf-8'),
            padding.PKCS1v15(),
            hashes.SHA1()
        )
        
        assinatura_base64 = base64.b64encode(assinatura).decode('utf-8')
        return assinatura_base64
    
    def string_nfe(self, dados):
        """Cria string para assinatura do RPS"""
        cdata = dados[0][:8].zfill(8)  # IE
        cdata += dados[1].ljust(5)  # Serie
        cdata += dados[2].zfill(12)  # Numero RPS
        cdata += dados[3][-4:] + dados[3][3:5] + dados[3][0:2]  # Data
        cdata += dados[4]  # tipo_recolhimento
        cdata += dados[5]  # Status do RPS
        cdata += dados[6]  # iss_retido S SIM - N NÃO
        valor = round(float(str(dados[7]).replace(",", "."))*100, 2)
        cdata += str(int(valor)).zfill(15)  # valor_servico
        cdata += str(int(float(str(dados[8]).replace(",", "."))*100)).zfill(15)  # valor_deducao
        cdata += dados[9].zfill(5)  # codigo_atividade
        cdata += dados[10]  # tipo_cpfcnpj
        cdata += dados[11].zfill(14)  # cnpj_cpf
        
        return cdata
    
    def string_nfe_cancelamento(self, dados):
        """Cria string para assinatura de cancelamento"""
        cdata = dados[0][:8].zfill(8)  # IE
        cdata += dados[1].zfill(12)  # Numero NF
        return cdata
    
    def criar_pedido_envio_rps(self, nota_fiscal):
        """
        Cria XML para envio de RPS
        
        Args:
            nota_fiscal: Instância do modelo NotaFiscalSP
        """
        # Prepara dados
        valor_servico = self.formata_valor(nota_fiscal.valor_total).replace(",", ".")
        valor_deducao = self.formata_valor(nota_fiscal.deducoes).replace(",", ".")
        aliquota = str(float(nota_fiscal.aliquota) / 100)
        data_rps = nota_fiscal.data_emissao.strftime('%Y-%m-%d') if nota_fiscal.data_emissao else datetime.now().strftime('%Y-%m-%d')
        
        # Determina se é CPF ou CNPJ do tomador
        cnpj_cpf_tomador = nota_fiscal.cnpj_cpf_tomador.replace('.', '').replace('/', '').replace('-', '')
        indicador_cnpj_cpf = "1" if len(cnpj_cpf_tomador) <= 11 else "2"
        
        # Data de emissão (usa data atual se não tiver)
        data_emissao = nota_fiscal.data_emissao if nota_fiscal.data_emissao else datetime.now().date()
        
        # Mapear status para código da API (N=Normal, C=Cancelada, E=Extraviada)
        status_map = {
            'pendente': 'N',
            'emitida': 'N',
            'cancelada': 'C',
            'erro': 'N'
        }
        status_rps_api = status_map.get(nota_fiscal.status_rps, 'N')
        
        # Dados para assinatura (ordem correta conforme NFeEventos.py)
        dados_ass = [
            self.inscricao_municipal,                                    # dados[0] - IE
            nota_fiscal.serie_rps or 'RPS',                             # dados[1] - Serie
            nota_fiscal.numero_rps or '1',                              # dados[2] - Numero RPS
            data_emissao.strftime('%d/%m/%Y'),                          # dados[3] - Data
            (nota_fiscal.tributacao_rps or nota_fiscal.tipo_tributacao)[:1],  # dados[4] - Tributacao
            status_rps_api,                                             # dados[5] - Status (N, C ou E)
            'S' if nota_fiscal.iss_retido else 'N',                    # dados[6] - ISS Retido
            valor_servico,                                              # dados[7] - Valor Servico
            valor_deducao,                                              # dados[8] - Valor Deducao
            nota_fiscal.cod_servico,                                    # dados[9] - Codigo Servico
            indicador_cnpj_cpf,                                         # dados[10] - Tipo CPF/CNPJ
            cnpj_cpf_tomador                                            # dados[11] - CPF/CNPJ
        ]
        
        # Define namespace
        nfe_namespace = "http://www.prefeitura.sp.gov.br/nfe"
        ET.register_namespace("p1", nfe_namespace)
        
        root = ET.Element("{%s}PedidoEnvioRPS" % nfe_namespace)
        
        # Cabecalho
        cabecalho = ET.SubElement(root, "Cabecalho", Versao="1")
        cpfcnpj_remetente = ET.SubElement(cabecalho, "CPFCNPJRemetente")
        ET.SubElement(cpfcnpj_remetente, "CNPJ").text = self.cnpj
        
        # RPS
        rps = ET.SubElement(root, "RPS")
        
        # Assinatura
        assinatura = ET.SubElement(rps, "Assinatura")
        assinatura.text = self.criar_assinatura_rps(dados_ass)
        
        # Chave RPS
        chave_rps = ET.SubElement(rps, "ChaveRPS")
        ET.SubElement(chave_rps, "InscricaoPrestador").text = self.inscricao_municipal
        ET.SubElement(chave_rps, "SerieRPS").text = nota_fiscal.serie_rps
        ET.SubElement(chave_rps, "NumeroRPS").text = str(nota_fiscal.numero_rps)
        
        # Dados do RPS
        ET.SubElement(rps, "TipoRPS").text = "RPS"
        ET.SubElement(rps, "DataEmissao").text = data_rps
        ET.SubElement(rps, "StatusRPS").text = status_rps_api  # N, C ou E
        ET.SubElement(rps, "TributacaoRPS").text = (nota_fiscal.tributacao_rps or nota_fiscal.tipo_tributacao)[:1]
        ET.SubElement(rps, "ValorServicos").text = valor_servico
        ET.SubElement(rps, "ValorDeducoes").text = valor_deducao
        
        # Valores retidos (se houver)
        if nota_fiscal.pis_retido:
            ET.SubElement(rps, "ValorPIS").text = self.formata_valor(nota_fiscal.pis_retido).replace(",", ".")
        if nota_fiscal.cofins_retido:
            ET.SubElement(rps, "ValorCOFINS").text = self.formata_valor(nota_fiscal.cofins_retido).replace(",", ".")
        if nota_fiscal.inss_retido:
            ET.SubElement(rps, "ValorINSS").text = self.formata_valor(nota_fiscal.inss_retido).replace(",", ".")
        if nota_fiscal.irrf_retido:
            ET.SubElement(rps, "ValorIR").text = self.formata_valor(nota_fiscal.irrf_retido).replace(",", ".")
        if nota_fiscal.csll_retido:
            ET.SubElement(rps, "ValorCSLL").text = self.formata_valor(nota_fiscal.csll_retido).replace(",", ".")
        
        ET.SubElement(rps, "CodigoServico").text = nota_fiscal.cod_servico
        ET.SubElement(rps, "AliquotaServicos").text = aliquota
        ET.SubElement(rps, "ISSRetido").text = "true" if nota_fiscal.iss_retido else "false"
        
        # Tomador
        cpfcnpj_tomador_elem = ET.SubElement(rps, "CPFCNPJTomador")
        if len(cnpj_cpf_tomador) <= 11:
            ET.SubElement(cpfcnpj_tomador_elem, "CPF").text = cnpj_cpf_tomador
        else:
            ET.SubElement(cpfcnpj_tomador_elem, "CNPJ").text = cnpj_cpf_tomador
        
        if nota_fiscal.nome_tomador:
            ET.SubElement(rps, "RazaoSocialTomador").text = nota_fiscal.nome_tomador
        
        ET.SubElement(rps, "Discriminacao").text = nota_fiscal.descricao
        
        # Signature (será preenchido na assinatura XML)
        signature = ET.SubElement(root, "{http://www.w3.org/2000/09/xmldsig#}Signature")
        signed_info = ET.SubElement(signature, "{http://www.w3.org/2000/09/xmldsig#}SignedInfo")
        ET.SubElement(signed_info, "{http://www.w3.org/2000/09/xmldsig#}CanonicalizationMethod", 
                     Algorithm="http://www.w3.org/TR/2001/REC-xml-c14n-20010315")
        ET.SubElement(signed_info, "{http://www.w3.org/2000/09/xmldsig#}SignatureMethod", 
                     Algorithm="http://www.w3.org/2000/09/xmldsig#rsa-sha1")
        reference = ET.SubElement(signed_info, "{http://www.w3.org/2000/09/xmldsig#}Reference", URI="")
        transforms = ET.SubElement(reference, "{http://www.w3.org/2000/09/xmldsig#}Transforms")
        ET.SubElement(transforms, "{http://www.w3.org/2000/09/xmldsig#}Transform", 
                     Algorithm="http://www.w3.org/2000/09/xmldsig#enveloped-signature")
        ET.SubElement(transforms, "{http://www.w3.org/2000/09/xmldsig#}Transform", 
                     Algorithm="http://www.w3.org/TR/2001/REC-xml-c14n-20010315")
        ET.SubElement(reference, "{http://www.w3.org/2000/09/xmldsig#}DigestMethod", 
                     Algorithm="http://www.w3.org/2000/09/xmldsig#sha1")
        ET.SubElement(reference, "{http://www.w3.org/2000/09/xmldsig#}DigestValue")
        ET.SubElement(signature, "{http://www.w3.org/2000/09/xmldsig#}SignatureValue")
        key_info = ET.SubElement(signature, "{http://www.w3.org/2000/09/xmldsig#}KeyInfo")
        ET.SubElement(key_info, "{http://www.w3.org/2000/09/xmldsig#}X509Data")
        
        # Converte para string
        xml_string = ET.tostring(root, encoding="utf-8")
        return xml_string.decode("utf-8")
    
    def cancelamento_nfe(self, nota_fiscal):
        """
        Cria XML para cancelamento de NFS-e
        
        Args:
            nota_fiscal: Instância do modelo NotaFiscalSP
        """
        nfe_namespace = "http://www.prefeitura.sp.gov.br/nfe"
        ET.register_namespace("p1", nfe_namespace)
        
        root = ET.Element("{%s}PedidoCancelamentoNFe" % nfe_namespace)
        
        # Cabecalho
        cabecalho = ET.SubElement(root, "Cabecalho", Versao="1")
        cpfcnpj_remetente = ET.SubElement(cabecalho, "CPFCNPJRemetente")
        ET.SubElement(cpfcnpj_remetente, "CNPJ").text = self.cnpj
        ET.SubElement(cabecalho, "transacao").text = "true"
        
        # Detalhe
        detalhe = ET.SubElement(root, "Detalhe")
        chave_nfe = ET.SubElement(detalhe, "ChaveNFe")
        ET.SubElement(chave_nfe, "InscricaoPrestador").text = self.inscricao_municipal
        ET.SubElement(chave_nfe, "NumeroNFe").text = str(nota_fiscal.numero_nfse)
        
        # Assinatura de cancelamento
        dados_cancel = [self.inscricao_municipal, str(nota_fiscal.numero_nfse)]
        assinatura = ET.SubElement(detalhe, "AssinaturaCancelamento")
        assinatura.text = self.criar_assinatura_rps(dados_cancel, cancelamento=True)
        
        # Signature
        signature = ET.SubElement(root, "{http://www.w3.org/2000/09/xmldsig#}Signature")
        signed_info = ET.SubElement(signature, "{http://www.w3.org/2000/09/xmldsig#}SignedInfo")
        ET.SubElement(signed_info, "{http://www.w3.org/2000/09/xmldsig#}CanonicalizationMethod", 
                     Algorithm="http://www.w3.org/TR/2001/REC-xml-c14n-20010315")
        ET.SubElement(signed_info, "{http://www.w3.org/2000/09/xmldsig#}SignatureMethod", 
                     Algorithm="http://www.w3.org/2000/09/xmldsig#rsa-sha1")
        reference = ET.SubElement(signed_info, "{http://www.w3.org/2000/09/xmldsig#}Reference", URI="")
        transforms = ET.SubElement(reference, "{http://www.w3.org/2000/09/xmldsig#}Transforms")
        ET.SubElement(transforms, "{http://www.w3.org/2000/09/xmldsig#}Transform", 
                     Algorithm="http://www.w3.org/2000/09/xmldsig#enveloped-signature")
        ET.SubElement(transforms, "{http://www.w3.org/2000/09/xmldsig#}Transform", 
                     Algorithm="http://www.w3.org/TR/2001/REC-xml-c14n-20010315")
        ET.SubElement(reference, "{http://www.w3.org/2000/09/xmldsig#}DigestMethod", 
                     Algorithm="http://www.w3.org/2000/09/xmldsig#sha1")
        ET.SubElement(reference, "{http://www.w3.org/2000/09/xmldsig#}DigestValue")
        ET.SubElement(signature, "{http://www.w3.org/2000/09/xmldsig#}SignatureValue")
        key_info = ET.SubElement(signature, "{http://www.w3.org/2000/09/xmldsig#}KeyInfo")
        ET.SubElement(key_info, "{http://www.w3.org/2000/09/xmldsig#}X509Data")
        
        xml_string = ET.tostring(root, encoding="utf-8")
        return xml_string.decode("utf-8")
    
    # Alias para compatibilidade
    def criar_pedido_cancelamento_nfe(self, nota_fiscal):
        """Alias para cancelamento_nfe"""
        return self.cancelamento_nfe(nota_fiscal)
    
    def pedidoConsultaNFPeriodo(self, cnpj_cpf, inscricao, data_inicio, data_fim):
        """
        Cria XML para consulta de NFS-e por período
        
        Args:
            cnpj_cpf: CNPJ ou CPF do contribuinte
            inscricao: Inscrição municipal
            data_inicio: Data inicial (formato: dd/mm/yyyy)
            data_fim: Data final (formato: dd/mm/yyyy)
        """
        # Converte datas
        data_init = data_inicio[-4:] + '-' + data_inicio[3:5] + '-' + data_inicio[0:2]
        data_fim_fmt = data_fim[-4:] + '-' + data_fim[3:5] + '-' + data_fim[0:2]
        
        namespace = "http://www.prefeitura.sp.gov.br/nfe"
        ET.register_namespace("p1", namespace)
        
        root = ET.Element("{%s}PedidoConsultaNFePeriodo" % namespace)
        cabecalho = ET.SubElement(root, "Cabecalho", Versao="1")
        
        cpf_cnpj_remetente = ET.SubElement(cabecalho, "CPFCNPJRemetente")
        ET.SubElement(cpf_cnpj_remetente, "CNPJ").text = cnpj_cpf
        
        cpf_cnpj = ET.SubElement(cabecalho, "CPFCNPJ")
        ET.SubElement(cpf_cnpj, "CNPJ").text = cnpj_cpf
        ET.SubElement(cabecalho, "Inscricao").text = inscricao
        ET.SubElement(cabecalho, "dtInicio").text = data_init
        ET.SubElement(cabecalho, "dtFim").text = data_fim_fmt
        ET.SubElement(cabecalho, "NumeroPagina").text = "1"
        
        # Signature
        signature = ET.SubElement(root, "{http://www.w3.org/2000/09/xmldsig#}Signature")
        signed_info = ET.SubElement(signature, "{http://www.w3.org/2000/09/xmldsig#}SignedInfo")
        ET.SubElement(signed_info, "{http://www.w3.org/2000/09/xmldsig#}CanonicalizationMethod", 
                     Algorithm="http://www.w3.org/TR/2001/REC-xml-c14n-20010315")
        ET.SubElement(signed_info, "{http://www.w3.org/2000/09/xmldsig#}SignatureMethod", 
                     Algorithm="http://www.w3.org/2000/09/xmldsig#rsa-sha1")
        reference = ET.SubElement(signed_info, "{http://www.w3.org/2000/09/xmldsig#}Reference", URI="")
        transforms = ET.SubElement(reference, "{http://www.w3.org/2000/09/xmldsig#}Transforms")
        ET.SubElement(transforms, "{http://www.w3.org/2000/09/xmldsig#}Transform", 
                     Algorithm="http://www.w3.org/2000/09/xmldsig#enveloped-signature")
        ET.SubElement(transforms, "{http://www.w3.org/2000/09/xmldsig#}Transform", 
                     Algorithm="http://www.w3.org/TR/2001/REC-xml-c14n-20010315")
        ET.SubElement(reference, "{http://www.w3.org/2000/09/xmldsig#}DigestMethod", 
                     Algorithm="http://www.w3.org/2000/09/xmldsig#sha1")
        ET.SubElement(reference, "{http://www.w3.org/2000/09/xmldsig#}DigestValue")
        ET.SubElement(signature, "{http://www.w3.org/2000/09/xmldsig#}SignatureValue")
        key_info = ET.SubElement(signature, "{http://www.w3.org/2000/09/xmldsig#}KeyInfo")
        ET.SubElement(key_info, "{http://www.w3.org/2000/09/xmldsig#}X509Data")
        
        xml_string = ET.tostring(root, encoding="utf-8")
        return xml_string.decode("utf-8")
    
    def criar_pedido_envio_nfts(self, nota_fiscal_tomador):
        """Cria XML para envio de NFTS"""
        valor_servico = self.formata_valor(nota_fiscal_tomador.valor_total).replace(",", ".")
        valor_deducao = self.formata_valor(nota_fiscal_tomador.deducoes).replace(",", ".")
        aliquota = str(float(nota_fiscal_tomador.aliquota) / 100)
        data_nfts = nota_fiscal_tomador.data_prestacao_servico.strftime('%Y-%m-%d')
        
        cnpj_cpf_prestador = nota_fiscal_tomador.cnpj_cpf_prestador.replace('.', '').replace('/', '').replace('-', '')
        cidade = nota_fiscal_tomador.cidade or ''
        estado = nota_fiscal_tomador.estado or ''
        cep = nota_fiscal_tomador.cep.replace('-', '') if nota_fiscal_tomador.cep else ''
        
        # Mapear tipo de documento para código da Prefeitura
        tipo_doc_map = {
            'nfe': '01',
            'nfse': '02',
            'cupom': '03',
            'recibo': '04'
        }
        tipo_documento_codigo = tipo_doc_map.get(nota_fiscal_tomador.tipo_documento.lower(), '02')
        
        # Mapear regime de tributação para código da Prefeitura (NFTS)
        # Valores válidos: 0 (Normal), 4 (Simples Nacional), 5 (MEI)
        regime_map = {
            'simples': '4',      # Simples Nacional
            'presumido': '0',    # Normal
            'real': '0',         # Normal
            'mei': '5'           # MEI - Microempreendedor Individual
        }
        regime_codigo = regime_map.get(nota_fiscal_tomador.regime_tributacao.lower(), '0')
        
        nfe_namespace = "http://www.prefeitura.sp.gov.br/nfts"
        ET.register_namespace("", nfe_namespace)  # Namespace padrão sem prefixo
        
        root = ET.Element("{%s}PedidoEnvioNFTS" % nfe_namespace)
        # Elementos internos SEM namespace (xmlns="")
        cabecalho = ET.SubElement(root, "Cabecalho", Versao="1")
        cabecalho.set("xmlns", "")  # Remove namespace
        cpfcnpj_remetente = ET.SubElement(cabecalho, "Remetente")
        cpf_cnpj = ET.SubElement(cpfcnpj_remetente, "CPFCNPJ")
        
        cnpj_tomador = nota_fiscal_tomador.cnpj_tomador.replace('.', '').replace('/', '').replace('-', '')
        if len(cnpj_tomador) <= 11:
            ET.SubElement(cpf_cnpj, "CPF").text = cnpj_tomador
        else:
            ET.SubElement(cpf_cnpj, "CNPJ").text = cnpj_tomador
        
        nfts = ET.SubElement(root, "tpNFTS")
        ET.SubElement(nfts, "TipoDocumento").text = tipo_documento_codigo
        chave_nfts = ET.SubElement(nfts, "ChaveDocumento")
        ET.SubElement(chave_nfts, "InscricaoMunicipal").text = nota_fiscal_tomador.inscricao_municipal
        if nota_fiscal_tomador.serie:
            ET.SubElement(chave_nfts, "SerieNFTS").text = nota_fiscal_tomador.serie[:5].strip()
        ET.SubElement(chave_nfts, "NumeroDocumento").text = nota_fiscal_tomador.numero_documento[:12]
        
        ET.SubElement(nfts, "DataPrestacao").text = data_nfts
        # StatusNFTS: "N" = Normal, "C" = Cancelada (sempre "N" na emissão)
        ET.SubElement(nfts, "StatusNFTS").text = "N"
        ET.SubElement(nfts, "TributacaoNFTS").text = nota_fiscal_tomador.tipo_tributacao[:1]
        ET.SubElement(nfts, "ValorServicos").text = valor_servico
        ET.SubElement(nfts, "ValorDeducoes").text = valor_deducao
        ET.SubElement(nfts, "CodigoServico").text = nota_fiscal_tomador.cod_servico[:4]
        ET.SubElement(nfts, "AliquotaServicos").text = aliquota
        ET.SubElement(nfts, "ISSRetidoTomador").text = "true" if nota_fiscal_tomador.iss_retido else "false"
        
        cpfcnpj_prestador_elem = ET.SubElement(nfts, "Prestador")
        cpf_cnpj_prest = ET.SubElement(cpfcnpj_prestador_elem, "CPFCNPJ")
        if len(cnpj_cpf_prestador) <= 11:
            ET.SubElement(cpf_cnpj_prest, "CPF").text = cnpj_cpf_prestador
        else:
            ET.SubElement(cpf_cnpj_prest, "CNPJ").text = cnpj_cpf_prestador
        
        endereco = ET.SubElement(cpfcnpj_prestador_elem, "Endereco")
        ET.SubElement(endereco, "Cidade").text = cidade
        ET.SubElement(endereco, "UF").text = estado
        if cep:
            ET.SubElement(endereco, "CEP").text = str(int(cep))
        
        ET.SubElement(nfts, "RegimeTributacao").text = regime_codigo
        ET.SubElement(nfts, "Discriminacao").text = nota_fiscal_tomador.descricao
        ET.SubElement(nfts, "TipoNFTS").text = '1'
        
        # Assinar ANTES de renomear (assina tpNFTS, não NFTS) - IGUAL AO CÓDIGO ORIGINAL
        xml_to_sign = ET.tostring(nfts, encoding="utf-8", method="xml").decode("utf-8")
        # Remover namespace (igual ao código original)
        xml_to_sign = xml_to_sign.replace(' xmlns:p1="http://www.prefeitura.sp.gov.br/nfts"', '')
        
        # DEBUG: Ver XML que será assinado
        print("=" * 80)
        print("XML QUE SERÁ ASSINADO (tpNFTS):")
        print(xml_to_sign[:500])
        print("=" * 80)
        
        caminho_pem = self.get_certificado_pem_path()
        # Carregar chave privada (igual ao código original)
        with open(caminho_pem, 'rb') as key_file:
            private_key = load_pem_private_key(key_file.read(), password=None, backend=default_backend())
        
        # Extrair certificado X509 do PEM para NFTS
        from cryptography import x509
        from cryptography.hazmat.primitives.serialization import Encoding
        
        with open(caminho_pem, 'rb') as cert_file:
            cert_pem = cert_file.read()
            # Encontrar o certificado (não a chave privada)
            cert_start = cert_pem.find(b'-----BEGIN CERTIFICATE-----')
            cert_end = cert_pem.find(b'-----END CERTIFICATE-----') + len(b'-----END CERTIFICATE-----')
            cert_data = cert_pem[cert_start:cert_end]
            certificate = x509.load_pem_x509_certificate(cert_data, default_backend())
            cert_base64 = base64.b64encode(certificate.public_bytes(Encoding.DER)).decode('utf-8')
        
        # Assinando o XML (PKCS1v15 + SHA1 - igual ao código original)
        signature = private_key.sign(
            xml_to_sign.encode('utf-8'),
            padding.PKCS1v15(),
            hashes.SHA1()
        )
        # Codificar a assinatura em Base64
        signature_base64 = base64.b64encode(signature).decode('utf-8')
        
        assinatura = ET.SubElement(nfts, "Assinatura")
        assinatura.text = signature_base64
        
        # Renomear a tag tpNFTS para NFTS (DEPOIS de assinar - igual ao código original)
        nfts.tag = "NFTS"
        # Remover namespace do elemento NFTS (xmlns="")
        nfts.set("xmlns", "")
        
        # Signature (com X509Certificate para NFTS)
        signature_elem = ET.SubElement(root, "{http://www.w3.org/2000/09/xmldsig#}Signature")
        signed_info = ET.SubElement(signature_elem, "{http://www.w3.org/2000/09/xmldsig#}SignedInfo")
        ET.SubElement(signed_info, "{http://www.w3.org/2000/09/xmldsig#}CanonicalizationMethod", 
                     Algorithm="http://www.w3.org/TR/2001/REC-xml-c14n-20010315")
        ET.SubElement(signed_info, "{http://www.w3.org/2000/09/xmldsig#}SignatureMethod", 
                     Algorithm="http://www.w3.org/2000/09/xmldsig#rsa-sha1")
        reference = ET.SubElement(signed_info, "{http://www.w3.org/2000/09/xmldsig#}Reference", URI="")
        transforms = ET.SubElement(reference, "{http://www.w3.org/2000/09/xmldsig#}Transforms")
        ET.SubElement(transforms, "{http://www.w3.org/2000/09/xmldsig#}Transform", 
                     Algorithm="http://www.w3.org/2000/09/xmldsig#enveloped-signature")
        ET.SubElement(transforms, "{http://www.w3.org/2000/09/xmldsig#}Transform", 
                     Algorithm="http://www.w3.org/TR/2001/REC-xml-c14n-20010315")
        ET.SubElement(reference, "{http://www.w3.org/2000/09/xmldsig#}DigestMethod", 
                     Algorithm="http://www.w3.org/2000/09/xmldsig#sha1")
        ET.SubElement(reference, "{http://www.w3.org/2000/09/xmldsig#}DigestValue")
        ET.SubElement(signature_elem, "{http://www.w3.org/2000/09/xmldsig#}SignatureValue")
        key_info = ET.SubElement(signature_elem, "{http://www.w3.org/2000/09/xmldsig#}KeyInfo")
        x509_data = ET.SubElement(key_info, "{http://www.w3.org/2000/09/xmldsig#}X509Data")
        x509_cert = ET.SubElement(x509_data, "{http://www.w3.org/2000/09/xmldsig#}X509Certificate")
        x509_cert.text = cert_base64
        
        # Converte a árvore XML para uma string formatada
        xml_string = ET.tostring(root, encoding="utf-8")
        
        return xml_string.decode("utf-8")
