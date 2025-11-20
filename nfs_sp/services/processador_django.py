"""
Processador de NFS-e para Django
Gerencia comunicação com webservices da Prefeitura de SP
"""
import xml.etree.ElementTree as ET
from lxml import etree
import xmlsec
import requests
from zeep import Client
from zeep.transports import Transport
from datetime import datetime
import locale

from .certificado_service import CertificadoService

# Configurar locale
try:
    locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')
except:
    try:
        locale.setlocale(locale.LC_ALL, '')
    except:
        pass


class ProcessadorNFeDjango:
    """
    Processa requisições SOAP para NFS-e São Paulo
    """
    
    def __init__(self, empresa):
        """
        Inicializa o processador
        
        Args:
            empresa: Instância do modelo Empresa do Django
        """
        self.empresa = empresa
        self.cert_service = CertificadoService()
        self.cert_path = self.cert_service.get_pem_path(empresa)
        
        # URLs dos webservices
        self.url_nfe = "https://nfe.prefeitura.sp.gov.br/ws/lotenfe.asmx?WSDL"
        self.url_nfts = "https://nfe.prefeitura.sp.gov.br/ws/loteNFTS.asmx?WSDL"
    
    def assinar_xml(self, xml_string):
        """
        Assina o XML com o certificado digital
        
        Args:
            xml_string: String do XML a ser assinado
            
        Returns:
            str: XML assinado
        """
        template = etree.fromstring(xml_string.encode('utf-8'))
        signature_node = xmlsec.tree.find_node(template, xmlsec.constants.NodeSignature)
        
        if not signature_node:
            raise Exception("Nó de assinatura não encontrado no XML")
        
        ctx = xmlsec.SignatureContext()
        
        # Carrega a chave do certificado
        key = xmlsec.Key.from_file(self.cert_path, xmlsec.constants.KeyDataFormatPem)
        key.load_cert_from_file(self.cert_path, xmlsec.constants.KeyDataFormatPem)
        ctx.key = key
        
        # Adiciona o nó de assinatura ao template
        if signature_node.getparent() is None:
            template.append(signature_node)
        
        # Assina o XML
        ctx.sign(signature_node)
        
        # Converte para string
        xml_bytes = etree.tostring(template, pretty_print=False, encoding="utf-8", xml_declaration=True)
        xml_str = xml_bytes.decode("utf-8")
        
        return xml_str
    
    def criar_cliente_soap(self, url):
        """
        Cria cliente SOAP com certificado
        
        Args:
            url: URL do WSDL
            
        Returns:
            Client: Cliente SOAP configurado
        """
        session = requests.Session()
        session.cert = self.cert_path
        transport = Transport(session=session)
        client = Client(url, transport=transport)
        return client
    
    def enviar_rps(self, xml_string):
        """
        Envia RPS para emissão de NFS-e
        
        Args:
            xml_string: XML do RPS assinado
            
        Returns:
            dict: Resultado do envio com sucesso, mensagem e dados da NFS-e
        """
        try:
            # Assina o XML
            xml_assinado = self.assinar_xml(xml_string)
            
            # Cria cliente SOAP
            client = self.criar_cliente_soap(self.url_nfe)
            
            # Envia RPS
            result = client.service.EnvioRPS(1, xml_assinado)
            
            # Processa resposta
            return self.processar_resposta_envio_rps(result)
            
        except Exception as e:
            return {
                'sucesso': False,
                'mensagem': f'Erro ao enviar RPS: {str(e)}',
                'erro': str(e)
            }
    
    def processar_resposta_envio_rps(self, xml_resposta):
        """
        Processa a resposta do envio de RPS
        
        Args:
            xml_resposta: XML de resposta do webservice
            
        Returns:
            dict: Dados processados da resposta
        """
        try:
            root = ET.fromstring(xml_resposta)
            
            # Tenta sem namespace primeiro (algumas respostas não têm namespace)
            sucesso_elem = root.find('.//Sucesso')
            if sucesso_elem is None:
                # Tenta com namespace
                namespace = {'nfe': 'http://www.prefeitura.sp.gov.br/nfe'}
                sucesso_elem = root.find('.//nfe:Sucesso', namespace)
            
            sucesso = sucesso_elem.text.lower() == 'true' if sucesso_elem is not None else False
            
            resultado = {
                'sucesso': sucesso,
                'xml_resposta': xml_resposta
            }
            
            if sucesso:
                # Extrai dados da NFS-e emitida (tenta sem namespace primeiro)
                chave_nfe = root.find('.//ChaveNFe')
                if chave_nfe is None:
                    # Tenta com namespace
                    namespace = {'nfe': 'http://www.prefeitura.sp.gov.br/nfe'}
                    chave_nfe = root.find('.//nfe:ChaveNFe', namespace)
                
                if chave_nfe is not None:
                    numero_nfe = chave_nfe.find('.//NumeroNFe')
                    if numero_nfe is None:
                        numero_nfe = chave_nfe.find('NumeroNFe')
                    
                    codigo_verificacao = chave_nfe.find('.//CodigoVerificacao')
                    if codigo_verificacao is None:
                        codigo_verificacao = chave_nfe.find('CodigoVerificacao')
                    
                    resultado['numero_nfe'] = numero_nfe.text if numero_nfe is not None else None
                    resultado['codigo_verificacao'] = codigo_verificacao.text if codigo_verificacao is not None else None
                    resultado['mensagem'] = 'NFS-e emitida com sucesso!'
                else:
                    # Se não encontrou ChaveNFe, tenta buscar NumeroNFe diretamente
                    numero_nfe = root.find('.//NumeroNFe')
                    codigo_verificacao = root.find('.//CodigoVerificacao')
                    
                    resultado['numero_nfe'] = numero_nfe.text if numero_nfe is not None else None
                    resultado['codigo_verificacao'] = codigo_verificacao.text if codigo_verificacao is not None else None
                    resultado['mensagem'] = 'NFS-e emitida com sucesso!'
                
                # Monta URL de visualização
                if resultado.get('numero_nfe') and resultado.get('codigo_verificacao'):
                    inscricao = self.empresa.inscricao_municipal
                    resultado['url_nfe'] = (
                        f"https://nfe.prefeitura.sp.gov.br/contribuinte/notaprint.aspx?"
                        f"inscricao={inscricao}&nf={resultado['numero_nfe']}&"
                        f"verificacao={resultado['codigo_verificacao']}"
                    )
                
                # Log para debug
                import logging
                logger = logging.getLogger(__name__)
                logger.info(f"NFS-e emitida - Número: {resultado.get('numero_nfe')}, Código: {resultado.get('codigo_verificacao')}")
                
                # Verifica alertas
                alertas = root.findall('.//Alerta')
                if not alertas:
                    namespace = {'nfe': 'http://www.prefeitura.sp.gov.br/nfe'}
                    alertas = root.findall('.//nfe:Alerta', namespace)
                if alertas:
                    resultado['alertas'] = []
                    for alerta in alertas:
                        codigo = alerta.find('.//Codigo', namespace)
                        descricao = alerta.find('.//Descricao', namespace)
                        resultado['alertas'].append({
                            'codigo': codigo.text if codigo is not None else '',
                            'descricao': descricao.text if descricao is not None else ''
                        })
            else:
                # Extrai erros
                erros = root.findall('.//Erro')
                if not erros:
                    namespace = {'nfe': 'http://www.prefeitura.sp.gov.br/nfe'}
                    erros = root.findall('.//nfe:Erro', namespace)
                
                if erros:
                    resultado['erros'] = []
                    for erro in erros:
                        codigo = erro.find('.//Codigo')
                        if codigo is None:
                            codigo = erro.find('Codigo')
                        descricao = erro.find('.//Descricao')
                        if descricao is None:
                            descricao = erro.find('Descricao')
                        resultado['erros'].append({
                            'codigo': codigo.text if codigo is not None else '',
                            'descricao': descricao.text if descricao is not None else ''
                        })
                    resultado['mensagem'] = resultado['erros'][0]['descricao'] if resultado['erros'] else 'Erro desconhecido'
                else:
                    resultado['mensagem'] = 'Erro ao emitir NFS-e'
            
            return resultado
            
        except Exception as e:
            return {
                'sucesso': False,
                'mensagem': f'Erro ao processar resposta: {str(e)}',
                'erro': str(e),
                'xml_resposta': xml_resposta
            }
    
    def cancelar_nfe(self, xml_string):
        """
        Cancela uma NFS-e
        
        Args:
            xml_string: XML de cancelamento assinado
            
        Returns:
            dict: Resultado do cancelamento
        """
        try:
            # Assina o XML
            xml_assinado = self.assinar_xml(xml_string)
            
            # Cria cliente SOAP
            client = self.criar_cliente_soap(self.url_nfe)
            
            # Cancela NFS-e
            result = client.service.CancelamentoNFe(1, xml_assinado)
            
            # Processa resposta
            return self.processar_resposta_cancelamento(result)
            
        except Exception as e:
            return {
                'sucesso': False,
                'mensagem': f'Erro ao cancelar NFS-e: {str(e)}',
                'erro': str(e)
            }
    
    def processar_resposta_cancelamento(self, xml_resposta):
        """
        Processa a resposta do cancelamento
        
        Args:
            xml_resposta: XML de resposta do webservice
            
        Returns:
            dict: Dados processados da resposta
        """
        try:
            root = ET.fromstring(xml_resposta)
            namespace = {'nfe': 'http://www.prefeitura.sp.gov.br/nfe'}
            
            # Verifica sucesso
            sucesso_elem = root.find('.//Sucesso', namespace)
            sucesso = sucesso_elem.text.lower() == 'true' if sucesso_elem is not None else False
            
            resultado = {
                'sucesso': sucesso,
                'xml_resposta': xml_resposta
            }
            
            if sucesso:
                resultado['mensagem'] = 'NFS-e cancelada com sucesso!'
            else:
                # Extrai erros
                erros = root.findall('.//Erro', namespace)
                if erros:
                    resultado['erros'] = []
                    for erro in erros:
                        codigo = erro.find('.//Codigo', namespace)
                        descricao = erro.find('.//Descricao', namespace)
                        resultado['erros'].append({
                            'codigo': codigo.text if codigo is not None else '',
                            'descricao': descricao.text if descricao is not None else ''
                        })
                    resultado['mensagem'] = resultado['erros'][0]['descricao'] if resultado['erros'] else 'Erro desconhecido'
                else:
                    resultado['mensagem'] = 'Erro ao cancelar NFS-e'
            
            return resultado
            
        except Exception as e:
            return {
                'sucesso': False,
                'mensagem': f'Erro ao processar resposta: {str(e)}',
                'erro': str(e),
                'xml_resposta': xml_resposta
            }
    
    def consultar_nfe_periodo(self, xml_string, tipo='E'):
        """
        Consulta NFS-e por período (Emitidas ou Recebidas)
        
        Args:
            xml_string: XML de consulta assinado
            tipo: 'E' para Emitidas, 'R' para Recebidas
            
        Returns:
            dict: Resultado da consulta com lista de notas
        """
        try:
            # Assina o XML
            xml_assinado = self.assinar_xml(xml_string)
            
            # Cria cliente SOAP
            client = self.criar_cliente_soap(self.url_nfe)
            
            # Consulta NFS-e
            if tipo == 'E':
                result = client.service.ConsultaNFeEmitidas(1, xml_assinado)
            else:
                result = client.service.ConsultaNFeRecebidas(1, xml_assinado)
            
            # Processa resposta
            return self.processar_resposta_consulta(result, tipo)
            
        except Exception as e:
            return {
                'sucesso': False,
                'mensagem': f'Erro ao consultar NFS-e: {str(e)}',
                'erro': str(e)
            }
    
    def processar_resposta_consulta(self, xml_resposta, tipo):
        """
        Processa a resposta da consulta de NFS-e
        
        Args:
            xml_resposta: XML de resposta do webservice
            tipo: Tipo de consulta ('E' ou 'R')
            
        Returns:
            dict: Dados processados com lista de notas
        """
        try:
            root = ET.fromstring(xml_resposta)
            namespace = {'nfe': 'http://www.prefeitura.sp.gov.br/nfe'}
            
            resultado = {
                'sucesso': True,
                'tipo': 'Emitidas' if tipo == 'E' else 'Recebidas',
                'notas': [],
                'xml_resposta': xml_resposta
            }
            
            # Extrai notas
            for nfe in root.findall('.//NFe', namespace):
                nota = self.extrair_dados_nfe(nfe, namespace)
                resultado['notas'].append(nota)
            
            resultado['total'] = len(resultado['notas'])
            resultado['mensagem'] = f"{resultado['total']} nota(s) encontrada(s)"
            
            return resultado
            
        except Exception as e:
            return {
                'sucesso': False,
                'mensagem': f'Erro ao processar resposta: {str(e)}',
                'erro': str(e),
                'xml_resposta': xml_resposta
            }
    
    def extrair_dados_nfe(self, nfe_element, namespace):
        """
        Extrai dados de um elemento NFe do XML
        
        Args:
            nfe_element: Elemento XML da NFe
            namespace: Namespace do XML
            
        Returns:
            dict: Dados da nota fiscal
        """
        def get_text(element, tag):
            child = element.find(tag, namespace)
            return child.text if child is not None else None
        
        def formata_valor(valor):
            if valor:
                try:
                    return str(locale.currency(float(valor), grouping=True, symbol=False))
                except:
                    return valor
            return ''
        
        def formata_data(data):
            if data:
                try:
                    return datetime.strptime(data, "%Y-%m-%dT%H:%M:%S").strftime("%d/%m/%Y %H:%M:%S")
                except:
                    return data
            return ''
        
        nota = {
            'inscricao_prestador': get_text(nfe_element, './/InscricaoPrestador'),
            'numero_nfe': get_text(nfe_element, './/NumeroNFe'),
            'codigo_verificacao': get_text(nfe_element, './/CodigoVerificacao'),
            'data_emissao': formata_data(get_text(nfe_element, './/DataEmissaoNFe')),
            'data_fato_gerador': formata_data(get_text(nfe_element, './/DataFatoGeradorNFe')),
            'cnpj_prestador': get_text(nfe_element, './/CNPJ'),
            'razao_social_prestador': get_text(nfe_element, './/RazaoSocialPrestador'),
            'logradouro': get_text(nfe_element, './/Logradouro'),
            'numero_endereco': get_text(nfe_element, './/NumeroEndereco'),
            'bairro': get_text(nfe_element, './/Bairro'),
            'cidade': get_text(nfe_element, './/Cidade'),
            'uf': get_text(nfe_element, './/UF'),
            'cep': get_text(nfe_element, './/CEP'),
            'status_nfe': get_text(nfe_element, './/StatusNFe'),
            'data_cancelamento': formata_data(get_text(nfe_element, './/DataCancelamento')),
            'tributacao_nfe': get_text(nfe_element, './/TributacaoNFe'),
            'valor_servicos': formata_valor(get_text(nfe_element, './/ValorServicos')),
            'codigo_servico': get_text(nfe_element, './/CodigoServico'),
            'aliquota_servicos': get_text(nfe_element, './/AliquotaServicos'),
            'valor_iss': formata_valor(get_text(nfe_element, './/ValorISS')),
            'valor_credito': formata_valor(get_text(nfe_element, './/ValorCredito')),
            'iss_retido': get_text(nfe_element, './/ISSRetido'),
            'discriminacao': get_text(nfe_element, './/Discriminacao'),
        }
        
        # CPF ou CNPJ do tomador
        cpf_tomador = get_text(nfe_element, './/CPFCNPJTomador/.//CPF')
        cnpj_tomador = get_text(nfe_element, './/CPFCNPJTomador/.//CNPJ')
        nota['cpf_cnpj_tomador'] = cpf_tomador if cpf_tomador else cnpj_tomador
        nota['razao_social_tomador'] = get_text(nfe_element, './/RazaoSocialTomador')
        
        return nota
    
    def enviar_nfts(self, xml_string):
        """
        Envia NFTS (Nota Fiscal do Tomador de Serviços)
        
        Args:
            xml_string: XML da NFTS já assinado
            
        Returns:
            dict: Resultado do envio
        """
        try:
            # O XML já vem assinado do criar_pedido_envio_nfts()
            # NÃO assinar novamente!
            
            # Cria cliente SOAP
            client = self.criar_cliente_soap(self.url_nfts)
            
            # Envia NFTS
            result = client.service.EnvioNFTS(xml_string)
            
            # Processa resposta (similar ao RPS)
            return self.processar_resposta_envio_rps(result)
            
        except Exception as e:
            return {
                'sucesso': False,
                'mensagem': f'Erro ao enviar NFTS: {str(e)}',
                'erro': str(e)
            }
