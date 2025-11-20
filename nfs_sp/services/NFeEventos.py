import xml.etree.ElementTree as ET
from xml.etree.ElementTree import Element, SubElement, tostring
import datetime
import locale
locale.setlocale(locale.LC_ALL, '')
#from DataBase.tabelas import Data_base
import sqlite3
#from funcoes.ui_function import consulta_cnpj, MsgBox
from functions import consultaDados_cnpj
from PySide6.QtWidgets import QMessageBox
from time import sleep

import lxml.etree as ET
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from cryptography.hazmat.backends import default_backend
import base64
import lxml.etree as ET
import xmlsec

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from cryptography.hazmat.primitives.serialization import load_pem_private_key
from cryptography.hazmat.backends import default_backend
import base64
from database import Data_base

from ibge.localidades import Municipios
import unidecode 

class EventoNFe():

    def __init__(self, cnpj) -> None:
        
        self.cnpj = cnpj
        self.db = Data_base()

    def criar_assinatura_rps(self, dados, cancelamento="N"):

        #cadeia_caracteres = "59073470001  00000000000120240430TNN00000000035950000000000000000006297100003752826703"
        if cancelamento == "S":
            cadeia_caracteres = self.string_nfe_cancelamento(dados)
        else:
            cadeia_caracteres = self.string_nfe(dados)
        #print(cadeia_caracteres)
        caminho_pem = self.db.criar_certificado_pem(self.cnpj)
        with open(caminho_pem, 'rb') as key_file: #'Certificados\\29797601000159.pem'
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
        assinatura = base64.b64encode(assinatura).decode('utf-8')
        #print(assinatura)
        return assinatura

    def pedidoConsultaGuiaAsync(self): # Evento de informacoes do contribuinte

        namespace = "http://www.prefeitura.sp.gov.br/nfe"

        ET.register_namespace("p1", namespace)
        # Cria o elemento raiz com o namespace padrão e prefixo "p1"
        root = ET.Element("{%s}PedidoConsultaGuia" % namespace)
        cpf_cnpj_remetente = ET.SubElement(root, "CPFCNPJRemetente")
        ET.SubElement(cpf_cnpj_remetente, "CNPJ").text = "44207820000124"
        ET.SubElement(root, "InscricaoPrestador").text = "71240233"
        ET.SubElement(root, "Incidencia").text = "2024-03"
        ET.SubElement(root, "Situacao").text = "3"
        #ET.SubElement(root, "TipoEmissao").text = "0"

        # # Criação do elemento <Signature> e seus subelementos
        # signature = ET.SubElement(root, "{http://www.w3.org/2000/09/xmldsig#}Signature")
        # signed_info = ET.SubElement(signature, "{http://www.w3.org/2000/09/xmldsig#}SignedInfo")
        # ET.SubElement(signed_info, "{http://www.w3.org/2000/09/xmldsig#}CanonicalizationMethod", Algorithm="http://www.w3.org/TR/2001/REC-xml-c14n-20010315")
        # ET.SubElement(signed_info, "{http://www.w3.org/2000/09/xmldsig#}SignatureMethod", Algorithm="http://www.w3.org/2000/09/xmldsig#rsa-sha1")
        # reference = ET.SubElement(signed_info, "{http://www.w3.org/2000/09/xmldsig#}Reference", URI="")
        # transforms = ET.SubElement(reference, "{http://www.w3.org/2000/09/xmldsig#}Transforms")
        # ET.SubElement(transforms, "{http://www.w3.org/2000/09/xmldsig#}Transform", Algorithm="http://www.w3.org/2000/09/xmldsig#enveloped-signature")
        # ET.SubElement(transforms, "{http://www.w3.org/2000/09/xmldsig#}Transform", Algorithm="http://www.w3.org/TR/2001/REC-xml-c14n-20010315")
        # ET.SubElement(reference, "{http://www.w3.org/2000/09/xmldsig#}DigestMethod", Algorithm="http://www.w3.org/2000/09/xmldsig#sha1")
        # ET.SubElement(reference, "{http://www.w3.org/2000/09/xmldsig#}DigestValue")

        # ET.SubElement(signature, "{http://www.w3.org/2000/09/xmldsig#}SignatureValue")

        # key_info = ET.SubElement(signature, "{http://www.w3.org/2000/09/xmldsig#}KeyInfo")
        # ET.SubElement(key_info, "{http://www.w3.org/2000/09/xmldsig#}X509Data")

        # Converte a árvore XML para uma string formatada
        xml_string = ET.tostring(root, encoding="utf-8")
        return xml_string.decode("utf-8")
    
    def pedidoEmissaoGuia(self): # Evento de informacoes do contribuinte       

        namespace = "http://www.prefeitura.sp.gov.br/nfe"
        xsi_namespace = "http://www.w3.org/2001/XMLSchema-instance"
        xsd_namespace = "http://www.w3.org/2001/XMLSchema"

        # Define o mapeamento de namespaces com o namespace padrão
        # nsmap = {
        #     None: namespace,  # Namespace padrão (sem prefixo)
        #     "xsi": xsi_namespace,
        #     "xsd": xsd_namespace
        # }
        ET.register_namespace("", namespace)  # Registra o namespace padrão
        root = ET.Element("{%s}PedidoEmissaoGuiaAsync" % namespace)
        # Cria o elemento raiz com o namespace e os prefixos definidos
        #root = ET.Element("{%s}PedidoEmissaoGuiaAsync" % namespace, nsmap=nsmap)

        # Cria o elemento CPFCNPJRemetente e seus subelementos
        cpfcnpj_remetente = ET.SubElement(root, "CPFCNPJRemetente")
        cnpj = ET.SubElement(cpfcnpj_remetente, "CNPJ")
        cnpj.text = "44207820000124"  # Insira o CNPJ desejado

        # Cria os demais elementos do pedido
        inscricao_prestador = ET.SubElement(root, "InscricaoPrestador")
        inscricao_prestador.text = "71240233"  # Insira a inscrição municipal desejada

        tipo_emissao_guia = ET.SubElement(root, "TipoEmissaoGuia")
        tipo_emissao_guia.text = "1"  # Insira o tipo de emissão desejado

        incidencia = ET.SubElement(root, "Incidencia")
        incidencia.text = "2024-03"  # Insira a incidência desejada

        data_pagamento = ET.SubElement(root, "DataPagamento")
        data_pagamento.text = "2024-04-01"  # Insira a data de pagamento desejada

        # Criação do elemento <Signature> e seus subelementos
        signature = ET.SubElement(root, "{http://www.w3.org/2000/09/xmldsig#}Signature")
        signed_info = ET.SubElement(signature, "{http://www.w3.org/2000/09/xmldsig#}SignedInfo")
        ET.SubElement(signed_info, "{http://www.w3.org/2000/09/xmldsig#}CanonicalizationMethod", Algorithm="http://www.w3.org/TR/2001/REC-xml-c14n-20010315")
        ET.SubElement(signed_info, "{http://www.w3.org/2000/09/xmldsig#}SignatureMethod", Algorithm="http://www.w3.org/2000/09/xmldsig#rsa-sha1")
        reference = ET.SubElement(signed_info, "{http://www.w3.org/2000/09/xmldsig#}Reference", URI="")
        transforms = ET.SubElement(reference, "{http://www.w3.org/2000/09/xmldsig#}Transforms")
        ET.SubElement(transforms, "{http://www.w3.org/2000/09/xmldsig#}Transform", Algorithm="http://www.w3.org/2000/09/xmldsig#enveloped-signature")
        ET.SubElement(transforms, "{http://www.w3.org/2000/09/xmldsig#}Transform", Algorithm="http://www.w3.org/TR/2001/REC-xml-c14n-20010315")
        ET.SubElement(reference, "{http://www.w3.org/2000/09/xmldsig#}DigestMethod", Algorithm="http://www.w3.org/2000/09/xmldsig#sha1")
        ET.SubElement(reference, "{http://www.w3.org/2000/09/xmldsig#}DigestValue")

        ET.SubElement(signature, "{http://www.w3.org/2000/09/xmldsig#}SignatureValue")

        key_info = ET.SubElement(signature, "{http://www.w3.org/2000/09/xmldsig#}KeyInfo")
        ET.SubElement(key_info, "{http://www.w3.org/2000/09/xmldsig#}X509Data")

        # Converte a árvore XML para uma string formatada
        xml_string = ET.tostring(root, encoding="utf-8")
        return xml_string.decode("utf-8")

    def pedidoConsultaNF(self): # Evento de informacoes do contribuinte       
        
        # Define o namespace padrão e o namespace xsi
        namespace = "http://www.prefeitura.sp.gov.br/nfe"
        ET.register_namespace("p1", namespace)
        # Cria o elemento raiz com o namespace padrão e prefixo "p1"
        root = ET.Element("{%s}PedidoConsultaNFe" % namespace)
        # Cria o elemento Cabecalho com o atributo Versao definido como "1"
        cabecalho = ET.SubElement(root, "Cabecalho", Versao="1")
        # Adiciona o elemento "CPFCNPJRemetente" com elemento "CNPJ"
        cpf_cnpj_remetente = ET.SubElement(cabecalho, "CPFCNPJRemetente")
        ET.SubElement(cpf_cnpj_remetente, "CNPJ").text = "29797601000159"

        # Adiciona o primeiro elemento "Detalhe"
        detalhe_nfe = ET.SubElement(root, "Detalhe")
        #Adiciona o elemento "ChaveNFe" com elementos "InscricaoPrestador" e "NumeroNFe"
        chave_nfe = ET.SubElement(detalhe_nfe, "ChaveNFe")
        ET.SubElement(chave_nfe, "InscricaoPrestador").text = "59073470"
        ET.SubElement(chave_nfe, "NumeroNFe").text = "6379"
        # Adiciona o segundo elemento "Detalhe"
        #detalhe_rps = ET.SubElement(root, "Detalhe")

        # Adiciona o elemento "ChaveRPS" com elementos "InscricaoPrestador", "SerieRPS" e "NumeroRPS"
        # chave_rps = ET.SubElement(detalhe_rps, "ChaveRPS")
        # ET.SubElement(chave_rps, "InscricaoPrestador").text = "71240233"
        # ET.SubElement(chave_rps, "SerieRPS").text = "BB"
        # ET.SubElement(chave_rps, "NumeroRPS").text = "4106"

        # Criação do elemento <Signature> e seus subelementos
        signature = ET.SubElement(root, "{http://www.w3.org/2000/09/xmldsig#}Signature")
        signed_info = ET.SubElement(signature, "{http://www.w3.org/2000/09/xmldsig#}SignedInfo")
        ET.SubElement(signed_info, "{http://www.w3.org/2000/09/xmldsig#}CanonicalizationMethod", Algorithm="http://www.w3.org/TR/2001/REC-xml-c14n-20010315")
        ET.SubElement(signed_info, "{http://www.w3.org/2000/09/xmldsig#}SignatureMethod", Algorithm="http://www.w3.org/2000/09/xmldsig#rsa-sha1")
        reference = ET.SubElement(signed_info, "{http://www.w3.org/2000/09/xmldsig#}Reference", URI="")
        transforms = ET.SubElement(reference, "{http://www.w3.org/2000/09/xmldsig#}Transforms")
        ET.SubElement(transforms, "{http://www.w3.org/2000/09/xmldsig#}Transform", Algorithm="http://www.w3.org/2000/09/xmldsig#enveloped-signature")
        ET.SubElement(transforms, "{http://www.w3.org/2000/09/xmldsig#}Transform", Algorithm="http://www.w3.org/TR/2001/REC-xml-c14n-20010315")
        ET.SubElement(reference, "{http://www.w3.org/2000/09/xmldsig#}DigestMethod", Algorithm="http://www.w3.org/2000/09/xmldsig#sha1")
        ET.SubElement(reference, "{http://www.w3.org/2000/09/xmldsig#}DigestValue")

        ET.SubElement(signature, "{http://www.w3.org/2000/09/xmldsig#}SignatureValue")

        key_info = ET.SubElement(signature, "{http://www.w3.org/2000/09/xmldsig#}KeyInfo")
        ET.SubElement(key_info, "{http://www.w3.org/2000/09/xmldsig#}X509Data")

        # Converte a árvore XML para uma string formatada
        xml_string = ET.tostring(root, encoding="utf-8")
        return xml_string.decode("utf-8")
    
    def pedidoConsultaNFPeriodo(self, CNPJ_CFP, IE, data_init, data_fim): # PEDIDO de consulta de NFS-e Emitidas ou Recebidas por período      
        
        data_init = data_init[-4:] + '-' + data_init[3:5] + '-' + data_init[0:2] 
        data_fim = data_fim[-4:] + '-' + data_fim[3:5] + '-' + data_fim[0:2] 
        # Define o namespace padrão e o namespace xsi
        namespace = "http://www.prefeitura.sp.gov.br/nfe"
        ET.register_namespace("p1", namespace)
        # Cria o elemento raiz com o namespace padrão e prefixo "p1"
        root = ET.Element("{%s}PedidoConsultaNFePeriodo" % namespace)
        # Cria o elemento Cabecalho com o atributo Versao definido como "1"
        cabecalho = ET.SubElement(root, "Cabecalho", Versao="1")
        # Adiciona o elemento "CPFCNPJRemetente" com elemento "CNPJ"
        cpf_cnpj_remetente = ET.SubElement(cabecalho, "CPFCNPJRemetente")
        ET.SubElement(cpf_cnpj_remetente, "CNPJ").text = CNPJ_CFP #CNPJ ou CPF

        cpf_cnpj = ET.SubElement(cabecalho, "CPFCNPJ")
        ET.SubElement(cpf_cnpj, "CNPJ").text = CNPJ_CFP #CNPJ ou CPF
        ET.SubElement(cabecalho, "Inscricao").text = IE
        ET.SubElement(cabecalho, "dtInicio").text = data_init
        ET.SubElement(cabecalho, "dtFim").text = data_fim
        ET.SubElement(cabecalho, "NumeroPagina").text = "1"
        
        # Criação do elemento <Signature> e seus subelementos
        signature = ET.SubElement(root, "{http://www.w3.org/2000/09/xmldsig#}Signature")
        signed_info = ET.SubElement(signature, "{http://www.w3.org/2000/09/xmldsig#}SignedInfo")
        ET.SubElement(signed_info, "{http://www.w3.org/2000/09/xmldsig#}CanonicalizationMethod", Algorithm="http://www.w3.org/TR/2001/REC-xml-c14n-20010315")
        ET.SubElement(signed_info, "{http://www.w3.org/2000/09/xmldsig#}SignatureMethod", Algorithm="http://www.w3.org/2000/09/xmldsig#rsa-sha1")
        reference = ET.SubElement(signed_info, "{http://www.w3.org/2000/09/xmldsig#}Reference", URI="")
        transforms = ET.SubElement(reference, "{http://www.w3.org/2000/09/xmldsig#}Transforms")
        ET.SubElement(transforms, "{http://www.w3.org/2000/09/xmldsig#}Transform", Algorithm="http://www.w3.org/2000/09/xmldsig#enveloped-signature")
        ET.SubElement(transforms, "{http://www.w3.org/2000/09/xmldsig#}Transform", Algorithm="http://www.w3.org/TR/2001/REC-xml-c14n-20010315")
        ET.SubElement(reference, "{http://www.w3.org/2000/09/xmldsig#}DigestMethod", Algorithm="http://www.w3.org/2000/09/xmldsig#sha1")
        ET.SubElement(reference, "{http://www.w3.org/2000/09/xmldsig#}DigestValue")

        ET.SubElement(signature, "{http://www.w3.org/2000/09/xmldsig#}SignatureValue")

        key_info = ET.SubElement(signature, "{http://www.w3.org/2000/09/xmldsig#}KeyInfo")
        ET.SubElement(key_info, "{http://www.w3.org/2000/09/xmldsig#}X509Data")

        # Converte a árvore XML para uma string formatada
        xml_string = ET.tostring(root, encoding="utf-8")
        return xml_string.decode("utf-8")
    
    def criar_pedido_consulta_cnpj(self):
        # Define o namespace para o prefixo p1
        nfe_namespace = "http://www.prefeitura.sp.gov.br/nfe"

        ET.register_namespace("p1", nfe_namespace)  # Registra o namespace padrão

        root = ET.Element("{%s}PedidoConsultaCNPJ" % nfe_namespace)
        # Cria o elemento Cabecalho com o atributo Versao definido como "1"
        cabecalho = ET.SubElement(root, "Cabecalho", Versao="1")

        # Adiciona o elemento CPFCNPJRemetente dentro de Cabecalho
        cpfcnpj_remetente = ET.SubElement(cabecalho, "CPFCNPJRemetente")
        cnpj_remetente = ET.SubElement(cpfcnpj_remetente, "CNPJ")
        cnpj_remetente.text = "44207820000124"  # Insira o CNPJ desejado

        # Cria o elemento CNPJContribuinte
        cnpj_contribuinte = ET.SubElement(root, "CNPJContribuinte")
        cnpj = ET.SubElement(cnpj_contribuinte, "CNPJ")
        cnpj.text = "44207820000124"  # Insira o CNPJ desejado

        # Criação do elemento <Signature> e seus subelementos
        signature = ET.SubElement(root, "{http://www.w3.org/2000/09/xmldsig#}Signature")
        signed_info = ET.SubElement(signature, "{http://www.w3.org/2000/09/xmldsig#}SignedInfo")
        ET.SubElement(signed_info, "{http://www.w3.org/2000/09/xmldsig#}CanonicalizationMethod", Algorithm="http://www.w3.org/TR/2001/REC-xml-c14n-20010315")
        ET.SubElement(signed_info, "{http://www.w3.org/2000/09/xmldsig#}SignatureMethod", Algorithm="http://www.w3.org/2000/09/xmldsig#rsa-sha1")
        reference = ET.SubElement(signed_info, "{http://www.w3.org/2000/09/xmldsig#}Reference", URI="")
        transforms = ET.SubElement(reference, "{http://www.w3.org/2000/09/xmldsig#}Transforms")
        ET.SubElement(transforms, "{http://www.w3.org/2000/09/xmldsig#}Transform", Algorithm="http://www.w3.org/2000/09/xmldsig#enveloped-signature")
        ET.SubElement(transforms, "{http://www.w3.org/2000/09/xmldsig#}Transform", Algorithm="http://www.w3.org/TR/2001/REC-xml-c14n-20010315")
        ET.SubElement(reference, "{http://www.w3.org/2000/09/xmldsig#}DigestMethod", Algorithm="http://www.w3.org/2000/09/xmldsig#sha1")
        ET.SubElement(reference, "{http://www.w3.org/2000/09/xmldsig#}DigestValue")

        ET.SubElement(signature, "{http://www.w3.org/2000/09/xmldsig#}SignatureValue")

        key_info = ET.SubElement(signature, "{http://www.w3.org/2000/09/xmldsig#}KeyInfo")
        ET.SubElement(key_info, "{http://www.w3.org/2000/09/xmldsig#}X509Data")

        # Converte a árvore XML para uma string formatada
        xml_string = ET.tostring(root, encoding="utf-8")
        
        return xml_string.decode("utf-8")

    def formata_valor(self, valor):
        
        if not valor :
            return ''
        retorno = str(locale.currency(float(valor), grouping =False, symbol=False)) if valor is not None or '' else ''
        return retorno
    
    def criar_pedido_envio_rps(self, cnpj, dados):
                
        valor_servico = self.formata_valor(dados[17]).replace(",",".")#'40.20' #str(int(float(dados[17].replace(",","."))*100))#.zfill(15) # valor_servico*
        valor_deducao =  self.formata_valor(dados[18]).replace(",",".")#'0'#str(int(float(dados[18].replace(",","."))*100))#.zfill(15) # valor_deducao*
        aliquota = str(float(dados[19].replace(",","."))/100)
        data_rps = dados[3][-4:] + '-' + dados[3][3:5] + '-' + dados[3][0:2] 
        pis_retido = self.formata_valor(dados[25]).replace(",",".")
        cofins_retido = self.formata_valor(dados[26]).replace(",",".")
        irrf_retido = self.formata_valor(dados[27]).replace(",",".")
        csll_retido = self.formata_valor(dados[28]).replace(",",".")
        inss_retido = self.formata_valor(dados[29]).replace(",",".")
        
        cnpj_cpf_tomador = len(dados[6])
        if cnpj_cpf_tomador <= 11:
            indicador_cnpj_cpf = "1"
        else:
            indicador_cnpj_cpf = "2"
        #dados = ['59073470', '001', "0002","24/07/2024", "T","N","N", "40,20", "0", "6297","1","03752826703"]
        dados_ass = [dados[5], dados[2], dados[1], dados[3], dados[20][:1], dados[21][:1],  dados[22][:1],
                     valor_servico, valor_deducao, dados[15], indicador_cnpj_cpf, dados[6]]
        # Define o namespace padrão
        nfe_namespace = "http://www.prefeitura.sp.gov.br/nfe"

        ET.register_namespace("p1", nfe_namespace)  # Registra o namespace padrão

        root = ET.Element("{%s}PedidoEnvioRPS" % nfe_namespace)
        # Cria o elemento Cabecalho com o atributo Versao
        cabecalho = ET.SubElement(root, "Cabecalho", Versao="1")
        # Adiciona o elemento CPFCNPJRemetente dentro de Cabecalho
        cpfcnpj_remetente = ET.SubElement(cabecalho, "CPFCNPJRemetente")
        ET.SubElement(cpfcnpj_remetente, "CNPJ").text = str(cnpj)  # Insira o CNPJ desejado
        # Cria o elemento RPS dentro do root
        rps = ET.SubElement(root, "RPS")
       
        # Faz assinatura do RPS
        assinatura = ET.SubElement(rps, "Assinatura")
        assin = self.criar_assinatura_rps(dados_ass)
        assinatura.text = assin
        
        # Adiciona os elementos dentro de RPS
        chave_rps = ET.SubElement(rps, "ChaveRPS")
        ET.SubElement(chave_rps, "InscricaoPrestador").text = dados[5]
        ET.SubElement(chave_rps, "SerieRPS").text = dados[2]
        ET.SubElement(chave_rps, "NumeroRPS").text = dados[1]
        ET.SubElement(rps, "TipoRPS").text = "RPS"
        ET.SubElement(rps, "DataEmissao").text = data_rps # "2024-07-24"
        ET.SubElement(rps, "StatusRPS").text = dados[21][:1]
        ET.SubElement(rps, "TributacaoRPS").text = dados[20][:1]
        ET.SubElement(rps, "ValorServicos").text = valor_servico
        ET.SubElement(rps, "ValorDeducoes").text = valor_deducao
        if pis_retido:
            ET.SubElement(rps, "ValorPIS").text = pis_retido
        if cofins_retido:
            ET.SubElement(rps, "ValorCOFINS").text = cofins_retido
        if inss_retido:
            ET.SubElement(rps, "ValorINSS").text = inss_retido
        if irrf_retido:
            ET.SubElement(rps, "ValorIR").text = irrf_retido
        if csll_retido:
            ET.SubElement(rps, "ValorCSLL").text = csll_retido
        ET.SubElement(rps, "CodigoServico").text = dados[15] #"6297"
        ET.SubElement(rps, "AliquotaServicos").text = aliquota #dados[19]
        ET.SubElement(rps, "ISSRetido").text = dados[22] = "false" if dados[22] == "NÃO" else "true"# "false"
        # Adiciona o elemento CPFCNPJTomador dentro de RPS
        cpfcnpj_tomador = ET.SubElement(rps, "CPFCNPJTomador")

        if cnpj_cpf_tomador <= 11:
            ET.SubElement(cpfcnpj_tomador, "CPF").text = dados[6]
            if dados[7]:
                ET.SubElement(rps, "RazaoSocialTomador").text = dados[7]
        else:
            ET.SubElement(cpfcnpj_tomador, "CNPJ").text = dados[6]
            if dados[7]:
                ET.SubElement(rps, "RazaoSocialTomador").text = dados[7]
        
            # # Cria o elemento EnderecoTomador
            # endereco_tomador = ET.SubElement(rps, "EnderecoTomador")
            # ET.SubElement(endereco_tomador, "TipoLogradouro").text = "R"
            # ET.SubElement(endereco_tomador, "Logradouro").text = dados[9]
            # ET.SubElement(endereco_tomador, "NumeroEndereco").text = dados[10]
            # #ET.SubElement(endereco_tomador, "ComplementoEndereco").text = dados[11]
            # ET.SubElement(endereco_tomador, "Bairro").text = dados[11]
            # ET.SubElement(endereco_tomador, "Cidade").text = dados[12]
            # ET.SubElement(endereco_tomador, "UF").text = dados[13]
            # ET.SubElement(endereco_tomador, "CEP").text = dados[7]
            # ET.SubElement(rps, "EmailTomador").text = dados[14]
        ET.SubElement(rps, "Discriminacao").text = dados[16]

        # Criação do elemento <Signature> e seus subelementos
        signature = ET.SubElement(root, "{http://www.w3.org/2000/09/xmldsig#}Signature")
        signed_info = ET.SubElement(signature, "{http://www.w3.org/2000/09/xmldsig#}SignedInfo")
        ET.SubElement(signed_info, "{http://www.w3.org/2000/09/xmldsig#}CanonicalizationMethod", Algorithm="http://www.w3.org/TR/2001/REC-xml-c14n-20010315")
        ET.SubElement(signed_info, "{http://www.w3.org/2000/09/xmldsig#}SignatureMethod", Algorithm="http://www.w3.org/2000/09/xmldsig#rsa-sha1")
        reference = ET.SubElement(signed_info, "{http://www.w3.org/2000/09/xmldsig#}Reference", URI="")
        transforms = ET.SubElement(reference, "{http://www.w3.org/2000/09/xmldsig#}Transforms")
        ET.SubElement(transforms, "{http://www.w3.org/2000/09/xmldsig#}Transform", Algorithm="http://www.w3.org/2000/09/xmldsig#enveloped-signature")
        ET.SubElement(transforms, "{http://www.w3.org/2000/09/xmldsig#}Transform", Algorithm="http://www.w3.org/TR/2001/REC-xml-c14n-20010315")
        ET.SubElement(reference, "{http://www.w3.org/2000/09/xmldsig#}DigestMethod", Algorithm="http://www.w3.org/2000/09/xmldsig#sha1")
        ET.SubElement(reference, "{http://www.w3.org/2000/09/xmldsig#}DigestValue")
        ET.SubElement(signature, "{http://www.w3.org/2000/09/xmldsig#}SignatureValue")
        key_info = ET.SubElement(signature, "{http://www.w3.org/2000/09/xmldsig#}KeyInfo")
        ET.SubElement(key_info, "{http://www.w3.org/2000/09/xmldsig#}X509Data")

        # Converte a árvore XML para uma string formatada
        xml_string = ET.tostring(root, encoding="utf-8")
        
        return xml_string.decode("utf-8")

    def string_nfe(self, dados):

        cdata =  dados[0][:8].zfill(8) # IE
        cdata += dados[1].ljust(5) # Serie
        cdata += dados[2].zfill(12) # Numero RPS
        cdata += dados[3][-4:] + dados[3][3:5] + dados[3][0:2] # Data
        cdata += dados[4] # tipo_recolhimento
        cdata += dados[5] # Status do RPS
        cdata += dados[6] # iss_retido S SIM - N NÃO
        valor = round(float(dados[7].replace(",","."))*100,2)
        cdata += str(int(valor)).zfill(15) # valor_servico*
        cdata += str(int(float(dados[8].replace(",","."))*100)).zfill(15) # valor_deducao*
        cdata += dados[9].zfill(5) # codigo_atividade.zfill(5)
        cdata += dados[10]  # tipo_cpfcnpj
        cdata += dados[11].zfill(14) # cnpj_cpf).zfill(14)
        # Incluir intermediario caso necessário

        return cdata

    def string_nfe_cancelamento(self, dados):

        cdata =  dados[0][:8].zfill(8) # IE
        cdata += dados[1].zfill(12) # Numero NF
        
        return cdata
    
    def cancelamento_nfe(self, dados):

        cnpj_remetente = dados[4] #"29797601000159" 
        im_prestador = dados[5] #"59073470"
        numero_nfe = dados[28] #"5949"

        nfe_namespace = "http://www.prefeitura.sp.gov.br/nfe"
        
        dados = [im_prestador, numero_nfe]

        ET.register_namespace("p1", nfe_namespace)  # Registra o namespace padrão

        root = ET.Element("{%s}PedidoCancelamentoNFe" % nfe_namespace)
        # Cria o elemento Cabecalho com o atributo Versao
        cabecalho = ET.SubElement(root, "Cabecalho", Versao="1")
        # Adiciona o elemento CPFCNPJRemetente dentro de Cabecalho
        cpfcnpj_remetente = ET.SubElement(cabecalho, "CPFCNPJRemetente")
        ET.SubElement(cpfcnpj_remetente, "CNPJ").text = cnpj_remetente  # Insira o CNPJ desejado
        ET.SubElement(cabecalho, "transacao").text = "true"

        # Cria o elemento Detalhe dentro do root
        detalhe = ET.SubElement(root, "Detalhe")

        # Cria o elemento ChaveNFe dentro de Detalhe
        chave_nfe = ET.SubElement(detalhe, "ChaveNFe")
        ET.SubElement(chave_nfe, "InscricaoPrestador").text = im_prestador
        ET.SubElement(chave_nfe, "NumeroNFe").text = numero_nfe

        # Faz assinatura para cancelamento da NFe
        assinatura = ET.SubElement(detalhe, "AssinaturaCancelamento")
        assin = self.criar_assinatura_rps(dados, "S")
        assinatura.text = assin

        # Criação do elemento <Signature> e seus subelementos
        signature = ET.SubElement(root, "{http://www.w3.org/2000/09/xmldsig#}Signature")
        signed_info = ET.SubElement(signature, "{http://www.w3.org/2000/09/xmldsig#}SignedInfo")
        ET.SubElement(signed_info, "{http://www.w3.org/2000/09/xmldsig#}CanonicalizationMethod", Algorithm="http://www.w3.org/TR/2001/REC-xml-c14n-20010315")
        ET.SubElement(signed_info, "{http://www.w3.org/2000/09/xmldsig#}SignatureMethod", Algorithm="http://www.w3.org/2000/09/xmldsig#rsa-sha1")
        reference = ET.SubElement(signed_info, "{http://www.w3.org/2000/09/xmldsig#}Reference", URI="")
        transforms = ET.SubElement(reference, "{http://www.w3.org/2000/09/xmldsig#}Transforms")
        ET.SubElement(transforms, "{http://www.w3.org/2000/09/xmldsig#}Transform", Algorithm="http://www.w3.org/2000/09/xmldsig#enveloped-signature")
        ET.SubElement(transforms, "{http://www.w3.org/2000/09/xmldsig#}Transform", Algorithm="http://www.w3.org/TR/2001/REC-xml-c14n-20010315")
        ET.SubElement(reference, "{http://www.w3.org/2000/09/xmldsig#}DigestMethod", Algorithm="http://www.w3.org/2000/09/xmldsig#sha1")
        ET.SubElement(reference, "{http://www.w3.org/2000/09/xmldsig#}DigestValue")
        ET.SubElement(signature, "{http://www.w3.org/2000/09/xmldsig#}SignatureValue")
        key_info = ET.SubElement(signature, "{http://www.w3.org/2000/09/xmldsig#}KeyInfo")
        ET.SubElement(key_info, "{http://www.w3.org/2000/09/xmldsig#}X509Data")

        # Converte a árvore XML para uma string formatada
        xml_string = ET.tostring(root, encoding="utf-8")

        return xml_string.decode("utf-8")
    
    def criar_pedido_envio_nfts(self, cnpj, dados):
        
        if len(dados[5]) <= 11:
            cidade = dados[8]
            estado = dados[9]
            cep = str(int(dados[10]))
        else:
            dados_cnpj = consultaDados_cnpj(dados[5])  
            cidade = dados_cnpj[5]
            estado = dados_cnpj[6]
            cep = str(int(dados_cnpj[7]))
        

        valor_servico = self.formata_valor(dados[13]).replace(",", ".")
        valor_deducao = self.formata_valor(dados[14]).replace(",", ".")
        aliquota = str(float(dados[15].replace(",", ".")) / 100)
        data_nfts = dados[4][-4:] + '-' + dados[4][3:5] + '-' + dados[4][0:2]

        cnpj_cpf_prestador = len(dados[5])
        indicador_cnpj_cpf = "1" if cnpj_cpf_prestador <= 11 else "2"

        nfe_namespace = "http://www.prefeitura.sp.gov.br/nfts"
        ET.register_namespace("p1", nfe_namespace)

        root = ET.Element("{%s}PedidoEnvioNFTS" % nfe_namespace)
        cabecalho = ET.SubElement(root, "Cabecalho", Versao="1")
        cpfcnpj_remetente = ET.SubElement(cabecalho, "Remetente")
        cpf_cnpj = ET.SubElement(cpfcnpj_remetente, "CPFCNPJ")

        if len(cnpj) <= 11:
            ET.SubElement(cpf_cnpj, "CPF").text = str(int(cnpj))
        else:
            ET.SubElement(cpf_cnpj, "CNPJ").text = str(int(cnpj))

        #nfts_root = ET.SubElement(root, "NFTS")
        nfts = ET.SubElement(root, "tpNFTS")
        ET.SubElement(nfts, "TipoDocumento").text = dados[18][:2]
        chave_nfts = ET.SubElement(nfts, "ChaveDocumento")
        ET.SubElement(chave_nfts, "InscricaoMunicipal").text = dados[3]
        serie = dados[7][:5].strip()
        if serie:
            ET.SubElement(chave_nfts, "SerieNFTS").text = serie
        ET.SubElement(chave_nfts, "NumeroDocumento").text = dados[6][:12]#'01'#

        ET.SubElement(nfts, "DataPrestacao").text = data_nfts
        ET.SubElement(nfts, "StatusNFTS").text = dados[19][:1]
        ET.SubElement(nfts, "TributacaoNFTS").text = dados[16][:1]
        ET.SubElement(nfts, "ValorServicos").text = valor_servico
        ET.SubElement(nfts, "ValorDeducoes").text = valor_deducao#'0'#valor_deducao

        ET.SubElement(nfts, "CodigoServico").text = dados[11][:4]
        ET.SubElement(nfts, "AliquotaServicos").text = aliquota#'0' #aliquota
        ET.SubElement(nfts, "ISSRetidoTomador").text = "false" if dados[20] == "NÃO" else "true"

        cpfcnpj_prestador = ET.SubElement(nfts, "Prestador")
        cpf_cnpj = ET.SubElement(cpfcnpj_prestador, "CPFCNPJ")
        if cnpj_cpf_prestador <= 11:
            ET.SubElement(cpf_cnpj, "CPF").text = str(int(dados[5]))
        else:
            ET.SubElement(cpf_cnpj, "CNPJ").text = str(int(dados[5]))
            #ET.SubElement(cpf_cnpj, "RazaoSocialTomador").text = dados[7]

        endereco = ET.SubElement(cpfcnpj_prestador, "Endereco")
        # ET.SubElement(endereco, "TipoLogradouro").text = "R"
        # ET.SubElement(endereco, "Logradouro").text = "CRAVOLANDIA"
        # ET.SubElement(endereco, "NumeroEndereco").text = "250"
        # #ET.SubElement(endereco, "ComplementoEndereco").text = dados[11]
        # ET.SubElement(endereco, "Bairro").text = "JARDIM PRESIDENTE DUTRA"
        
        ET.SubElement(endereco, "Cidade").text = cidade #"GUARULHOS" #   GUARULHOS 3518800
        ET.SubElement(endereco, "UF").text = estado #"SP"
        ET.SubElement(endereco, "CEP").text = cep #"7172120" # NÃO PODE TER ZERO A ESQUERDA
        #ET.SubElement(cpfcnpj_prestador, "Email").text = "teste@teste.com.br"

        ET.SubElement(nfts, "RegimeTributacao").text = dados[17][:1]
        ET.SubElement(nfts, "Discriminacao").text = dados[12]
        ET.SubElement(nfts, "TipoNFTS").text = '1'

        # Converte a árvore XML para uma string formatada sem a declaração XML
        #xml_string = ET.tostring(root, encoding="utf-8").decode("utf-8")
        xml_to_sign = ET.tostring(nfts, encoding="utf-8", method="xml").decode("utf-8")
        # Remover declaração XML (se houver)
        xml_to_sign = xml_to_sign.replace(' xmlns:p1="http://www.prefeitura.sp.gov.br/nfts"', '')
        #xml_to_sign = xml_to_sign.replace('NFTS', 'tpNFTS')
        caminho_pem = self.db.criar_certificado_pem(self.cnpj)
        # Carregar chave privada
        with open(caminho_pem, 'rb') as key_file:
            private_key = load_pem_private_key(key_file.read(), password=None, backend=default_backend())

        # Assinando o XML
        signature = private_key.sign(
            xml_to_sign.encode('utf-8'),
            padding.PKCS1v15(),
            hashes.SHA1()
        )
        # Codificar a assinatura em Base64
        signature_base64 = base64.b64encode(signature).decode('utf-8')

        assinatura = ET.SubElement(nfts, "Assinatura")
        # validar esses campos, estão apos a assinatura no documento
        # ET.SubElement(nfts, "CodigoCEI").text = '512223512071' # CodigoCEI
        # ET.SubElement(nfts, "MatriculaObra").text = '202000006376' # Número da matrícula de obra.

        assinatura.text = signature_base64
        
        # Renomear a tag tpNFTS para NFTS
        nfts.tag = "NFTS"

        # Criação do elemento <Signature> e seus subelementos
        signature = ET.SubElement(root, "{http://www.w3.org/2000/09/xmldsig#}Signature")
        signed_info = ET.SubElement(signature, "{http://www.w3.org/2000/09/xmldsig#}SignedInfo")
        ET.SubElement(signed_info, "{http://www.w3.org/2000/09/xmldsig#}CanonicalizationMethod", Algorithm="http://www.w3.org/TR/2001/REC-xml-c14n-20010315")
        ET.SubElement(signed_info, "{http://www.w3.org/2000/09/xmldsig#}SignatureMethod", Algorithm="http://www.w3.org/2000/09/xmldsig#rsa-sha1")
        reference = ET.SubElement(signed_info, "{http://www.w3.org/2000/09/xmldsig#}Reference", URI="")
        transforms = ET.SubElement(reference, "{http://www.w3.org/2000/09/xmldsig#}Transforms")
        ET.SubElement(transforms, "{http://www.w3.org/2000/09/xmldsig#}Transform", Algorithm="http://www.w3.org/2000/09/xmldsig#enveloped-signature")
        ET.SubElement(transforms, "{http://www.w3.org/2000/09/xmldsig#}Transform", Algorithm="http://www.w3.org/TR/2001/REC-xml-c14n-20010315")
        ET.SubElement(reference, "{http://www.w3.org/2000/09/xmldsig#}DigestMethod", Algorithm="http://www.w3.org/2000/09/xmldsig#sha1")
        ET.SubElement(reference, "{http://www.w3.org/2000/09/xmldsig#}DigestValue")
        ET.SubElement(signature, "{http://www.w3.org/2000/09/xmldsig#}SignatureValue")
        key_info = ET.SubElement(signature, "{http://www.w3.org/2000/09/xmldsig#}KeyInfo")
        ET.SubElement(key_info, "{http://www.w3.org/2000/09/xmldsig#}X509Data")
        
        # Converte a árvore XML para uma string formatada
        xml_string = ET.tostring(root, encoding="utf-8")

        return xml_string.decode("utf-8")

    def cancelamento_nfts(self, cnpj, dados):

        cnpj_remetente = cnpj #"29797601000159" 
        im_prestador = dados[3]#"59073470"
        numero_nfe = dados[21]#"12"

        nfts_namespace = "http://www.prefeitura.sp.gov.br/nfts"
        
        ET.register_namespace("p1", nfts_namespace)  # Registra o namespace padrão

        root = ET.Element("{%s}PedidoCancelamentoNFTS" % nfts_namespace)
        cabecalho = ET.SubElement(root, "Cabecalho", Versao="1")
        cpfcnpj_remetente = ET.SubElement(cabecalho, "Remetente")
        ET.SubElement(cabecalho, "transacao").text = 'true'

        cpf_cnpj = ET.SubElement(cpfcnpj_remetente, "CPFCNPJ")

        if len(cnpj_remetente) <= 11:
            ET.SubElement(cpf_cnpj, "CPF").text = cnpj_remetente
        else:
            ET.SubElement(cpf_cnpj, "CNPJ").text = cnpj_remetente


        # Cria o elemento Detalhe dentro do root
        detalhe = ET.SubElement(root, "DetalheNFTS")

        # Cria o elemento ChaveNFTS dentro de Detalhe
        chave_nfe = ET.SubElement(detalhe, "ChaveNFTS")
        ET.SubElement(chave_nfe, "InscricaoMunicipal").text = im_prestador
        ET.SubElement(chave_nfe, "NumeroNFTS").text = numero_nfe


        xml_to_sign = ET.tostring(detalhe, encoding="utf-8", method="xml").decode("utf-8")
        # Remover declaração XML (se houver)
        xml_to_sign = xml_to_sign.replace(' xmlns:p1="http://www.prefeitura.sp.gov.br/nfts"', '')
        xml_to_sign = xml_to_sign.replace('DetalheNFTS', 'PedidoCancelamentoNFTSDetalheNFTS')
        caminho_pem = self.db.criar_certificado_pem(self.cnpj)
        # Carregar chave privada
        with open(caminho_pem, 'rb') as key_file:
            private_key = load_pem_private_key(key_file.read(), password=None, backend=default_backend())

        # Assinando o XML
        signature = private_key.sign(
            xml_to_sign.encode('utf-8'),
            padding.PKCS1v15(),
            hashes.SHA1()
        )

        # Codificar a assinatura em Base64
        signature_base64 = base64.b64encode(signature).decode('utf-8')

        assinatura = ET.SubElement(detalhe, "AssinaturaCancelamento")
        assinatura.text = signature_base64

        # Criação do elemento <Signature> e seus subelementos
        signature = ET.SubElement(root, "{http://www.w3.org/2000/09/xmldsig#}Signature")
        signed_info = ET.SubElement(signature, "{http://www.w3.org/2000/09/xmldsig#}SignedInfo")
        ET.SubElement(signed_info, "{http://www.w3.org/2000/09/xmldsig#}CanonicalizationMethod", Algorithm="http://www.w3.org/TR/2001/REC-xml-c14n-20010315")
        ET.SubElement(signed_info, "{http://www.w3.org/2000/09/xmldsig#}SignatureMethod", Algorithm="http://www.w3.org/2000/09/xmldsig#rsa-sha1")
        reference = ET.SubElement(signed_info, "{http://www.w3.org/2000/09/xmldsig#}Reference", URI="")
        transforms = ET.SubElement(reference, "{http://www.w3.org/2000/09/xmldsig#}Transforms")
        ET.SubElement(transforms, "{http://www.w3.org/2000/09/xmldsig#}Transform", Algorithm="http://www.w3.org/2000/09/xmldsig#enveloped-signature")
        ET.SubElement(transforms, "{http://www.w3.org/2000/09/xmldsig#}Transform", Algorithm="http://www.w3.org/TR/2001/REC-xml-c14n-20010315")
        ET.SubElement(reference, "{http://www.w3.org/2000/09/xmldsig#}DigestMethod", Algorithm="http://www.w3.org/2000/09/xmldsig#sha1")
        ET.SubElement(reference, "{http://www.w3.org/2000/09/xmldsig#}DigestValue")
        ET.SubElement(signature, "{http://www.w3.org/2000/09/xmldsig#}SignatureValue")
        key_info = ET.SubElement(signature, "{http://www.w3.org/2000/09/xmldsig#}KeyInfo")
        ET.SubElement(key_info, "{http://www.w3.org/2000/09/xmldsig#}X509Data")

        # Converte a árvore XML para uma string formatada
        xml_string = ET.tostring(root, encoding="utf-8")

        return xml_string.decode("utf-8")
    
    def cod_ibge(self, municipio):
        try:
            data = Municipios()

            for i in data.json():
                if unidecode.unidecode(i['nome'].lower()) == unidecode.unidecode(municipio.lower()): # trazer aqui o nome da cidade dos "dados_fornec"
                    cod_municipio = i['id']
                    #print(cod_municipio)
                    break
            return cod_municipio
        except Exception as e:
            print(e)
            return ''
        

if __name__ == '__main__':
    
    dados = ['59073470', '001', "0001","18/08/2024", "T","N","N", "3595,00", "0", "6297","1","03752826703"]

    aa = EventoNFe('29797601000159')
    #app = aa.criar_pedido_envio_rps(dados)
    app = aa.string_nfe(dados)

    print(app)