from lxml import etree
import xmlsec
import requests
from time import sleep
from zeep import Client
from zeep.transports import Transport
import requests
from zeep import Client, Transport
from NFeEventos import EventoNFe
from database import Data_base
import xml.etree.ElementTree as ET
from datetime import datetime
import sqlite3
import locale
locale.setlocale(locale.LC_ALL, "")
from functions import MsgBox

db = Data_base()

#dados = ['59073470', '001', "0002","24/07/2024", "T","N","N", "40", "0", "6297","1","03752826703"]
# dados = ['59073470', '001', "0002","24/07/2024", "T","N","N", "40,20", "0", "6297","1","03752826703"]
# cnpj = "29797601000159"
# # IE = "59073470"
# # data_init = "2024-07-01"
# # data_fim = "2024-07-10"

# evento = EventoNFe(cnpj)
# #xml = evento.criar_pedido_consulta_cnpj()
# xml = evento.pedidoConsultaNF()
# #xml = evento.pedidoConsultaGuiaAsync()
# ## xml = evento.criar_pedido_envio_rps(cnpj, dados)
# #dados2 = ['59073470', '5949']
# #xml = evento.cancelamento_nfe(dados2)
# #xml = evento.pedidoConsultaNFPeriodo(cnpj, IE, data_init, data_fim)
# template = etree.fromstring(xml)
# signature_node = xmlsec.tree.find_node(template, xmlsec.constants.NodeSignature)
# ctx = xmlsec.SignatureContext()
# try:
#     caminho_pem = db.criar_certificado_pem(cnpj)
# except Exception as e :
#     print(e)
#     #return ['erro',f'Erro ao carregar certificado: <br>{e}','Erro ao carregar certificado']

# key = xmlsec.Key.from_file(caminho_pem, xmlsec.constants.KeyDataFormatPem)
# key.load_cert_from_file(caminho_pem, xmlsec.constants.KeyDataFormatPem) # 'Certificados\\29797601000159.pem'
# ctx.key = key
# template.append(signature_node)

# # Assina o XML
# ctx.sign(signature_node)

# # Transforma a estrutura XML (`template`) em uma string de bytes com codificação UTF-8
# xml_bytes = etree.tostring(template, pretty_print=False, encoding="utf-8", xml_declaration=True)

# # Decodifica a string de bytes para uma string com codificação UTF-8
# xml_str = xml_bytes.decode("utf-8")

class Processar():
    
    def pedidoConsultaCNPJ(self, xml_str):
            
        cert_path = 'Certificados\\29797601000159.pem'
        # Defina o endpoint do serviço
        url = "https://nfe.prefeitura.sp.gov.br/ws/lotenfe.asmx?WSDL"
        session = requests.Session()
        session.cert = cert_path

        # Configura o transporte com a sessão
        transport = Transport(session=session)
        # Crie o cliente com o transporte configurado
        client = Client(url, transport=transport)
        # Chame a função ConsultaNFe com a mensagem SOAP e o cabeçalho SOAPAction
        result = client.service.ConsultaCNPJ(1, xml_str)

        print(result)
    
    def pedidoConsultaNFe(self, xml_str):
            
        cert_path = 'Certificados\\29797601000159.pem'
        # Defina o endpoint do serviço
        url = "https://nfe.prefeitura.sp.gov.br/ws/lotenfe.asmx?WSDL"
        session = requests.Session()
        session.cert = cert_path

        # Configura o transporte com a sessão
        transport = Transport(session=session)
        # Crie o cliente com o transporte configurado
        client = Client(url, transport=transport)
        # Chame a função ConsultaNFe com a mensagem SOAP e o cabeçalho SOAPAction
        result = client.service.ConsultaNFe(1, xml_str)

        print(result)

    def pedidoConsultaNFePeriodo(self, xml_str, cert_path, tipo='E'):
        try:   
            #cert_path = 'Certificados\\29797601000159.pem'
            # Defina o endpoint do serviço
            url = "https://nfe.prefeitura.sp.gov.br/ws/lotenfe.asmx?WSDL"
            session = requests.Session()
            session.cert = cert_path

            # Configura o transporte com a sessão
            transport = Transport(session=session)
            # Crie o cliente com o transporte configurado
            client = Client(url, transport=transport)
            # Chame a função ConsultaNFe com a mensagem SOAP e o cabeçalho SOAPAction
            if tipo == 'E':
                result = client.service.ConsultaNFeEmitidas(1, xml_str)
                tipo = 'Emitidas'
            else:
                result = client.service.ConsultaNFeRecebidas(1, xml_str)
                tipo = 'Recebidas'

            # print(result)
            # with open("teste.xml","w", encoding="utf-8") as file:
            #     file.write(result)

            self.insert_notas_Emitidas(result, tipo)

            MsgBox("OK", f"Notas Inseridas com Sucesso!", "Consulta Notas")
            return "Ok"

        except Exception as e:
            MsgBox("ERRO", f"Consulta realizada com Erro!<br>{e}", "Consulta Notas")
    
    def pedidoConsultaGuiaAsyc(self, xml_str):
            
        cert_path = 'Certificados\\29797601000159.pem'
        # Defina o endpoint do serviço
        url = "https://nfews.prefeitura.sp.gov.br/lotenfeasync.asmx?WSDL"
        session = requests.Session()
        session.cert = cert_path

        # Configura o transporte com a sessão
        transport = Transport(session=session)
        # Crie o cliente com o transporte configurado
        client = Client(url, transport=transport)
        # Chame a função ConsultaNFe com a mensagem SOAP e o cabeçalho SOAPAction
        result = client.service.ConsultaGuia(1, xml_str)

        print(result)

    def pedidoEnvio_rps(self, xml_str, cert_path):
            
        #cert_path = 'Certificados\\29797601000159.pem'
        # Defina o endpoint do serviço
        url = "https://nfe.prefeitura.sp.gov.br/ws/lotenfe.asmx?WSDL"
        session = requests.Session()
        session.cert = cert_path

        # Configura o transporte com a sessão
        transport = Transport(session=session)
        # Crie o cliente com o transporte configurado
        client = Client(url, transport=transport)
        # Chame a função ConsultaNFe com a mensagem SOAP e o cabeçalho SOAPAction
        result = client.service.EnvioRPS(1, xml_str)
        #print(result)
        return result
        # https://nfe.prefeitura.sp.gov.br/contribuinte/notaprint.aspx?inscricao=59073470&nf=6379&verificacao=TSAX6E4F
    
    def pedido_cancelamento_nfe(self, xml_str, cert_path):
            
        #cert_path = 'Certificados\\29797601000159.pem'
        # Defina o endpoint do serviço
        url = "https://nfe.prefeitura.sp.gov.br/ws/lotenfe.asmx?WSDL"
        session = requests.Session()
        session.cert = cert_path

        # Configura o transporte com a sessão
        transport = Transport(session=session)
        # Crie o cliente com o transporte configurado
        client = Client(url, transport=transport)
        # Chame a função ConsultaNFe com a mensagem SOAP e o cabeçalho SOAPAction
        result = client.service.CancelamentoNFe(1, xml_str)

        #print(result)
        return result

    def get_text(self, element, tag):
        child = element.find(tag)
        return child.text if child is not None else None

    def formata_valor(self, valor):
        
        retorno = str(locale.currency(float(valor), grouping =True, symbol=False)) if valor is not None or '' else ''
        return retorno
    
    def formata_data(self, data):
        retorno = datetime.strptime(data , "%Y-%m-%dT%H:%M:%S").strftime("%d/%m/%Y %H:%M:%S") if data is not None or '' else ''
        return retorno
    
    def insert_notas_Emitidas(self, xml_str, tipo_nf):
        
        db.conecta()
        cursor = db.connection.cursor()   

        root = ET.fromstring(xml_str)
        # Definir o namespace a ser usado
        namespace = {'nfe': 'http://www.prefeitura.sp.gov.br/nfe'}

        try:
            # Itera sobre cada NFe no XML
            for nfe in root.findall('.//NFe', namespace):
                # Depurar: Imprimir o tag do elemento encontrado
                print(f"Processing element: {nfe.tag}")
                inscricao_prestador = self.get_text(nfe, './/InscricaoPrestador')
                numero_nfe = self.get_text(nfe, './/NumeroNFe')
                codigo_verificacao = self.get_text(nfe, './/CodigoVerificacao')
                data_emissao = self.formata_data(self.get_text(nfe, './/DataEmissaoNFe'))#datetime.strptime(self.get_text(nfe, './/DataEmissaoNFe'), "%Y-%m-%dT%H:%M:%S").strftime("%d/%m/%Y %H:%M:%S")
                data_fato_gerador = self.formata_data(self.get_text(nfe, './/DataFatoGeradorNFe'))#datetime.strptime(self.get_text(nfe, './/DataFatoGeradorNFe'), "%Y-%m-%dT%H:%M:%S").strftime("%d/%m/%Y %H:%M:%S")
                cnpj_prestador = self.get_text(nfe, './/CNPJ')
                razao_social_prestador = self.get_text(nfe, './/RazaoSocialPrestador')
                tipo_logradouro = self.get_text(nfe, './/TipoLogradouro')
                logradouro = self.get_text(nfe, './/Logradouro')
                numero_endereco = self.get_text(nfe, './/NumeroEndereco')
                complemento_endereco = self.get_text(nfe, './/ComplementoEndereco')
                bairro = self.get_text(nfe, './/Bairro')
                cidade = self.get_text(nfe, './/Cidade')
                uf = self.get_text(nfe, './/UF')
                cep = self.get_text(nfe, './/CEP')
                email_prestador = self.get_text(nfe, './/EmailPrestador')
                status_nfe = self.get_text(nfe, './/StatusNFe')
                data_cancelamento =  self.formata_data(self.get_text(nfe, './/DataCancelamento'))#datetime.strptime(self.get_text(nfe, './/DataCancelamento'), "%Y-%m-%dT%H:%M:%S").strftime("%d/%m/%Y %H:%M:%S")
                tributacao_nfe = self.get_text(nfe, './/TributacaoNFe')
                opcao_simples = self.get_text(nfe, './/OpcaoSimples')
                valor_servicos = self.get_text(nfe, './/ValorServicos')
                valor_servicos = self.formata_valor(valor_servicos)#str(locale.currency(float(valor_servicos), grouping =True, symbol=False))
                codigo_servico = self.get_text(nfe, './/CodigoServico')
                aliquota_servicos = self.get_text(nfe, './/AliquotaServicos').replace('.',',')
                valor_iss = self.get_text(nfe, './/ValorISS')
                valor_iss = self.formata_valor(valor_iss)#str(locale.currency(float(valor_iss), grouping =True, symbol=False))
                valor_credito = self.get_text(nfe, './/ValorCredito')
                valor_credito = self.formata_valor(valor_credito)#str(locale.currency(float(valor_credito), grouping =True, symbol=False))
                iss_retido = self.get_text(nfe, './/ISSRetido')
                cpf_cnpj_tomador = self.get_text(nfe, './/CPFCNPJTomador/.//CPF')
                if not cpf_cnpj_tomador:  # fallback to CNPJ if CPF is not available
                    cpf_cnpj_tomador = self.get_text(nfe, './/CPFCNPJTomador/.//CNPJ')
                razao_social_tomador = self.get_text(nfe, './/RazaoSocialTomador')
                discriminacao = self.get_text(nfe, './/Discriminacao')
                tipo = tipo_nf
                # Insere os dados na tabela
                insert_query = '''
                INSERT INTO NF_EMIT_RECEB (
                    inscricao_prestador, numero_nfe, codigo_verificacao, data_emissao,
                    data_fato_gerador, cnpj_prestador, razao_social_prestador, tipo_logradouro,
                    logradouro, numero_endereco, complemento_endereco, bairro, cidade, uf, cep,
                    email_prestador, status_nfe, data_cancelamento, tributacao_nfe, opcao_simples,
                    valor_servicos, codigo_servico, aliquota_servicos, valor_iss, valor_credito,
                    iss_retido, cpf_cnpj_tomador, razao_social_tomador, discriminacao, tipo
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,?)
                '''
                try:
                    cursor.execute(insert_query, (
                    inscricao_prestador, numero_nfe, codigo_verificacao, data_emissao,
                    data_fato_gerador, cnpj_prestador, razao_social_prestador, tipo_logradouro,
                    logradouro, numero_endereco, complemento_endereco, bairro, cidade, uf, cep,
                    email_prestador, status_nfe, data_cancelamento, tributacao_nfe, int(opcao_simples),
                    valor_servicos, codigo_servico, aliquota_servicos, valor_iss, valor_credito,
                    iss_retido.upper(), cpf_cnpj_tomador, razao_social_tomador.upper(), discriminacao, tipo
                    ))
                    db.connection.commit()
                except sqlite3.IntegrityError as e:
                    if "UNIQUE constraint failed" in str(e):
                        print(f"Erro Notas Emitidas: {e}")
                        continue
        except Exception as e:
            print("erro Notas Emitidas: ", e)

        db.close_connection()  
    
    def assinar_xml(self, xml, cnpj):
        
        template = etree.fromstring(xml)
        signature_node = xmlsec.tree.find_node(template, xmlsec.constants.NodeSignature)
        ctx = xmlsec.SignatureContext()
        try:
            caminho_pem = db.criar_certificado_pem(cnpj)
        except Exception as e :
            print(e)
            #return ['erro',f'Erro ao carregar certificado: <br>{e}','Erro ao carregar certificado']

        key = xmlsec.Key.from_file(caminho_pem, xmlsec.constants.KeyDataFormatPem)
        key.load_cert_from_file(caminho_pem, xmlsec.constants.KeyDataFormatPem) # 'Certificados\\29797601000159.pem'
        ctx.key = key
        template.append(signature_node)

        # Assina o XML
        ctx.sign(signature_node)

        # Transforma a estrutura XML (`template`) em uma string de bytes com codificação UTF-8
        xml_bytes = etree.tostring(template, pretty_print=False, encoding="utf-8", xml_declaration=True)

        # Decodifica a string de bytes para uma string com codificação UTF-8
        xml_str = xml_bytes.decode("utf-8")
        
        return xml_str

    def pedidoEnvio_nfts(self, xml_str, cert_path):
            
        #cert_path = 'Certificados\\29797601000159.pem'
        # Defina o endpoint do serviço
        url = "https://nfe.prefeitura.sp.gov.br/ws/loteNFTS.asmx?WSDL"
        session = requests.Session()
        session.cert = cert_path

        # Configura o transporte com a sessão
        transport = Transport(session=session)
        # Crie o cliente com o transporte configurado
        client = Client(url, transport=transport)
        # Chame a função ConsultaNFe com a mensagem SOAP e o cabeçalho SOAPAction
        result = client.service.EnvioNFTS(xml_str)
        print(result)
        return result

    def pedido_cancelamento_nfts(self, xml_str, cert_path):
            
        #cert_path = 'Certificados\\29797601000159.pem'
        # Defina o endpoint do serviço
        url = "https://nfe.prefeitura.sp.gov.br/ws/lotenfts.asmx?WSDL"
        session = requests.Session()
        session.cert = cert_path

        # Configura o transporte com a sessão
        transport = Transport(session=session)
        # Crie o cliente com o transporte configurado
        client = Client(url, transport=transport)
        # Chame a função ConsultaNFe com a mensagem SOAP e o cabeçalho SOAPAction
        result = client.service.CancelaNFTS(xml_str)

        print(result)
        return result
    


if __name__ == '__main__':
    
    aa = Processar()
    #app = aa.pedidoConsultaCNPJ(xml_str)
    #app = aa.pedidoConsultaNFe(xml_str)
    # app = aa.pedidoConsultaGuiaAsyc(xml_str)
    #app = aa.pedidoEnvio_rps(xml_str)
    #app = aa.pedidoConsultaNFePeriodo(xml_str,'E')
    #app = aa.pedido_cancelamento_nfe(xml_str)
    #print(app)
    # <?xml version="1.0" encoding="UTF-8"?><RetornoCancelamentoNFe xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns="http://www.prefeitura.sp.gov.br/nfe"><Cabecalho Versao="1" xmlns=""><Sucesso>true</Sucesso></Cabecalho></RetornoCancelamentoNFe>
    """
    <RetornoEnvioRPS xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns="http://www.prefeitura.sp.gov.br/nfe">
        <Cabecalho Versao="1" xmlns="">
            <Sucesso>true</Sucesso>
        </Cabecalho>
        <Alerta xmlns="">
            <Codigo>208</Codigo>
            <Descricao>Alíquota informada (5) difere da alíquota vigente (0,05) para o código de serviço informado. O sistema irá adotar a alíquota vigente.</Descricao>
            <ChaveRPS>
                <InscricaoPrestador>59073470</InscricaoPrestador>
                <SerieRPS>001</SerieRPS>
                <NumeroRPS>1</NumeroRPS>
            </ChaveRPS>
        </Alerta>
        <ChaveNFeRPS xmlns="">
            <ChaveNFe>
                <InscricaoPrestador>59073470</InscricaoPrestador>
                <NumeroNFe>5948</NumeroNFe>
                <CodigoVerificacao>M2UTLZ6X</CodigoVerificacao>
            </ChaveNFe>
            <ChaveRPS>
                <InscricaoPrestador>59073470</InscricaoPrestador>
                <SerieRPS>001</SerieRPS>
                <NumeroRPS>1</NumeroRPS>
            </ChaveRPS>
        </ChaveNFeRPS>
    </RetornoEnvioRPS>
    
    """