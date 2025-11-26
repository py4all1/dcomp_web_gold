import base64
import gzip
import requests
import logging
import time
from datetime import datetime, timedelta, timezone
from dataclasses import dataclass, field
from typing import Optional

# Para timezone de São Paulo
try:
    from zoneinfo import ZoneInfo
    SAO_PAULO_TZ = ZoneInfo('America/Sao_Paulo')
except ImportError:
    # Fallback para Python < 3.9
    try:
        import pytz
        SAO_PAULO_TZ = pytz.timezone('America/Sao_Paulo')
    except ImportError:
        # Se não tiver pytz, cria timezone fixo UTC-3
        SAO_PAULO_TZ = timezone(timedelta(hours=-3))

# Bibliotecas de assinatura e XML
from signxml import XMLSigner, methods
from lxml import etree

from warnings import filterwarnings

from signxml.algorithms import CanonicalizationMethod
filterwarnings('ignore')

# Configuração de Certificado (Fallback)
try:
    from certificado import listar_certificados, extrair_key_and_pem
    CERT_PEM = 'client_cert.pem'
    KEY_PEM = 'client_key.pem'
except ImportError:
    CERT_PEM = 'client_cert.pem' 
    KEY_PEM = 'client_key.pem'

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- DATACLASSES ---

@dataclass
class DadosEmitente:
    tipo_inscricao: str = "1"
    cnpj_cpf: str = "12345678000190"
    inscricao_municipal: Optional[str] = "3106200"
    razao_social: str = "Empresa Exemplo Ltda"
    cod_municipio: str = "3106200"

@dataclass
class DadosTomador:
    tipo_inscricao: str = "1"
    # CNPJ VÁLIDO (Gerado para teste)
    cnpj_cpf_nif: str = "47960950000121" 
    razao_social: str = "Tomador de Serviços Teste Ltda"
    logradouro: str = "Avenida Tomador"
    numero: str = "789"
    bairro: str = "Bairro Tomador"
    cod_municipio: str = "3106200"
    cep: str = "02000000"

@dataclass
class DadosPrestador:
    tipo_inscricao: str = "1"
    # OBS: Em produção/homologação real, este CNPJ deve ser o mesmo do certificado digital!
    # ESTE CNPJ PRECISA BATER COM O DO CERTIFICADO!
    cnpj_cpf_nif: str = "33291488000102"  # 33291488000102
    razao_social: Optional[str] = "Empresa Prestadora Teste Ltda"
    op_simples_nacional: str = "1"
    regime_especial_trib: str = "0"

@dataclass
class DadosServico:
    cod_municipio_prestacao: str = "3550308"
    cod_tributacao_nacional: str = "010101"
    descricao_servico: str = "Descrição completa do serviço"
    cod_nbs: Optional[str] = None 

@dataclass
class DadosValores:
    valor_servico: float = 0.1
    valor_liquido: float = 0.1

@dataclass
class DadosTributacao:
    tributacao_issqn: str = "1"
    tipo_retencao_issqn: str = "1"
    aliquota_issqn: Optional[float] = 0.1

@dataclass
class DadosNFSe:
    cod_municipio_emissor: str = "3106200"
    ambiente: str = "1" # 2=Homologação
    versao_aplicativo: str = "1.4.0"
    serie_dps: str = "00001"
    numero_dps: str = "1"
    data_competencia: str = None
    data_emissao: Optional[datetime] = None
    tipo_emitente: str = "1"
    
    emitente: DadosEmitente = field(default_factory=DadosEmitente)
    prestador: DadosPrestador = field(default_factory=DadosPrestador)
    tomador: DadosTomador = field(default_factory=DadosTomador)
    servico: DadosServico = field(default_factory=DadosServico)
    valores: DadosValores = field(default_factory=DadosValores)
    tributacao: DadosTributacao = field(default_factory=DadosTributacao)
    
    def __post_init__(self):
        if self.data_competencia is None:
            # Data de competência no horário de São Paulo (365 dias atrás)
            self.data_competencia = (datetime.now(SAO_PAULO_TZ) - timedelta(days=365)).strftime("%Y-%m-%d")
        if self.data_emissao is None:
            # Data de emissão no horário de São Paulo, 2 minutos no passado para evitar erro de processamento
            self.data_emissao = datetime.now(SAO_PAULO_TZ) - timedelta(minutes=2)
            
        self.serie_dps = str(self.serie_dps).zfill(5)

# --- PROCESSADOR ---

class ProcessadorNFSeNacional:
    
    def __init__(self):
        self.session = requests.Session()
        if CERT_PEM and KEY_PEM:
            try:
                self.session.cert = (CERT_PEM, KEY_PEM)
            except Exception:
                pass

    @staticmethod
    def gzip_base64_xml(xml_bytes: bytes) -> str:
        gz = gzip.compress(xml_bytes)
        return base64.b64encode(gz).decode('ascii')

    @staticmethod
    def gerar_id_inf_dps(cod_mun, tipo_insc, insc_fed, serie, num_dps):
        cod_mun = str(cod_mun).zfill(7)
        insc_fed = str(insc_fed).replace('.', '').replace('/', '').replace('-', '').zfill(14)
        serie = str(serie).zfill(5)
        num_dps = str(num_dps).zfill(15)
        print(f"DPS-{cod_mun}-{tipo_insc}-{insc_fed}-{serie}-{num_dps}")
        return f"DPS{cod_mun}{tipo_insc}{insc_fed}{serie}{num_dps}"

    @staticmethod
    def gerar_xml_dps(dados: DadosNFSe) -> str:
        def fmt_data(dt: datetime) -> str:
            # Garante que a data está no timezone de São Paulo e formata corretamente
            if dt.tzinfo is None:
                # Se não tem timezone, assume que já está no horário de São Paulo
                dt = dt.replace(tzinfo=SAO_PAULO_TZ)
            else:
                # Converte para o horário de São Paulo se estiver em outro timezone
                dt = dt.astimezone(SAO_PAULO_TZ)
            
            # Formata no horário de São Paulo: -03:00 ou -02:00 (ajusta automaticamente para horário de verão)
            # O strftime com %z retorna +HHMM ou -HHMM, precisamos converter para +HH:MM ou -HH:MM
            tz_offset = dt.strftime("%z")
            if tz_offset:
                # Formata o offset como -03:00 ou -02:00
                offset_formatted = f"{tz_offset[:3]}:{tz_offset[3:]}"
                return dt.strftime("%Y-%m-%dT%H:%M:%S") + offset_formatted
            else:
                # Fallback caso não consiga obter o offset
                return dt.strftime("%Y-%m-%dT%H:%M:%S-03:00")
        
        def fmt_val(v: Optional[float]) -> str:
            return f"{v:.2f}" if v is not None else None
            
        def tag(name, val, indent=4):
            if val is None: return ""
            return f"{' ' * indent}<{name}>{val}</{name}>\n"

        id_dps = ProcessadorNFSeNacional.gerar_id_inf_dps(
            dados.cod_municipio_emissor, 
            dados.prestador.tipo_inscricao,
            dados.prestador.cnpj_cpf_nif,
            dados.serie_dps,
            dados.numero_dps
        )

        xml = '<?xml version="1.0" encoding="UTF-8"?>\n'
        xml += '<DPS xmlns="http://www.sped.fazenda.gov.br/nfse" versao="1.00">\n'
        xml += f'  <infDPS Id="{id_dps}">\n'
        
        xml += tag('tpAmb', dados.ambiente)
        xml += tag('dhEmi', fmt_data(dados.data_emissao))
        xml += tag('verAplic', dados.versao_aplicativo)
        xml += tag('serie', dados.serie_dps)
        xml += tag('nDPS', dados.numero_dps)
        xml += tag('dCompet', dados.data_competencia)
        xml += tag('tpEmit', dados.tipo_emitente)
        xml += tag('cLocEmi', dados.cod_municipio_emissor)
        
        xml += '    <prest>\n'
        if dados.prestador.tipo_inscricao == "1":
            xml += tag('CNPJ', dados.prestador.cnpj_cpf_nif, 6)
        elif dados.prestador.tipo_inscricao == "2":
            xml += tag('CPF', dados.prestador.cnpj_cpf_nif, 6)
        xml += tag('xNome', dados.prestador.razao_social, 6)
        xml += '      <regTrib>\n'
        xml += tag('opSimpNac', dados.prestador.op_simples_nacional, 8)
        xml += tag('regEspTrib', dados.prestador.regime_especial_trib, 8)
        xml += '      </regTrib>\n'
        xml += '    </prest>\n'

        xml += '    <toma>\n'
        if dados.tomador.tipo_inscricao == "1":
            xml += tag('CNPJ', dados.tomador.cnpj_cpf_nif, 6)
        elif dados.tomador.tipo_inscricao == "2":
            xml += tag('CPF', dados.tomador.cnpj_cpf_nif, 6)
        xml += tag('xNome', dados.tomador.razao_social, 6)
        if dados.tomador.logradouro:
            xml += '      <end>\n'
            xml += '        <endNac>\n'
            xml += tag('cMun', dados.tomador.cod_municipio, 10)
            xml += tag('CEP', dados.tomador.cep, 10)
            xml += '        </endNac>\n'
            xml += tag('xLgr', dados.tomador.logradouro, 8)
            xml += tag('nro', dados.tomador.numero, 8)
            xml += tag('xBairro', dados.tomador.bairro, 8)
            xml += '      </end>\n'
        xml += '    </toma>\n'

        xml += '    <serv>\n'
        xml += '      <locPrest>\n'
        xml += tag('cLocPrestacao', dados.servico.cod_municipio_prestacao, 8)
        xml += '      </locPrest>\n'
        xml += '      <cServ>\n'
        xml += tag('cTribNac', dados.servico.cod_tributacao_nacional, 8)
        xml += tag('xDescServ', dados.servico.descricao_servico, 8)
        # cNBS removido
        xml += '      </cServ>\n'
        xml += '    </serv>\n'

        xml += '    <valores>\n'
        xml += '      <vServPrest>\n'
        xml += tag('vServ', fmt_val(dados.valores.valor_servico), 8)
        xml += '      </vServPrest>\n'
        
        # --- CORREÇÃO: Adicionada a tag totTrib obrigatória ---
        xml += '      <trib>\n'
        
        # 1. Tributação Municipal
        xml += '        <tribMun>\n'
        xml += tag('tribISSQN', dados.tributacao.tributacao_issqn, 10)
        xml += tag('tpRetISSQN', dados.tributacao.tipo_retencao_issqn, 10)
        xml += tag('pAliq', fmt_val(dados.tributacao.aliquota_issqn), 10)
        xml += '        </tribMun>\n'
        
        # 2. Total Tributos (Lei da Transparência) - Obrigatório
        # Usamos indTotTrib=0 (Sem informação)
        xml += '        <totTrib>\n'
        xml += '          <indTotTrib>0</indTotTrib>\n'
        xml += '        </totTrib>\n'
        
        xml += '      </trib>\n'
        xml += '    </valores>\n'

        xml += '  </infDPS>\n'
        xml += '</DPS>'
        return xml

    @staticmethod
    def sign_xml_string(xml_string: str, cert_pem_path: str, key_pem_path: str) -> bytes:
        """
        Assina a tag infDPS, garante as 2 Transforms requeridas e move a assinatura 
        para a posição correta (filha de DPS) para cumprir o XSD da SEFIN.
        """
        import os
        
        # Verifica se os arquivos PEM existem
        if not os.path.exists(key_pem_path):
            raise FileNotFoundError(f"Arquivo de chave nao encontrado: {key_pem_path}")
        if not os.path.exists(cert_pem_path):
            raise FileNotFoundError(f"Arquivo de certificado nao encontrado: {cert_pem_path}")
        
        # 1. Preparação
        if xml_string.strip().startswith('<?xml'):
            xml_string = xml_string.split('?>', 1)[1]

        parser = etree.XMLParser(remove_blank_text=True)
        root = etree.fromstring(xml_string.encode('utf-8'), parser=parser)
        
        ns = {"n": "http://www.sped.fazenda.gov.br/nfse", "ds": "http://www.w3.org/2000/09/xmldsig#"}
        
        ref_node = root.find(".//n:infDPS", namespaces=ns) or root.find(".//infDPS")
        if ref_node is None:
            raise ValueError("infDPS nao encontrado para assinatura")
        
        id_infdps = ref_node.get("Id")

        # Lê os arquivos PEM
        with open(key_pem_path, 'rb') as f: 
            key_data = f.read()
        with open(cert_pem_path, 'rb') as f: 
            cert_data = f.read()
        
        # Verifica se os arquivos têm conteúdo
        if len(key_data) == 0:
            raise ValueError("Arquivo de chave esta vazio")
        if len(cert_data) == 0:
            raise ValueError("Arquivo de certificado esta vazio")
        
        # 2. Configuração e Execução da Assinatura
        signer = XMLSigner(
            method=methods.enveloped,
            signature_algorithm="rsa-sha256",
            digest_algorithm="sha256",
            # Define o C14N Exclusive para o SignedInfo (Importante!)
            c14n_algorithm="http://www.w3.org/2001/10/xml-exc-c14n#",
        )
        
        # Assina infDPS
        # IMPORTANTE: Com methods.enveloped, a assinatura é inserida DENTRO do elemento assinado
        try:
            # Verifica XML antes
            xml_antes = etree.tostring(root, encoding='unicode', pretty_print=True)

            
            # IMPORTANTE: O reference_uri deve apontar para o ID do elemento que está sendo assinado
            # Tenta assinar o ref_node - o sign() retorna o elemento assinado
            
            # TENTATIVA 1: Assinar o ref_node (infDPS) diretamente - isso deve inserir a assinatura DENTRO do infDPS
            try:
                signed_element = signer.sign(
                    ref_node, 
                    key=key_data, 
                    cert=cert_data, 
                    reference_uri="#" + id_infdps
                )
                
                # Verifica imediatamente se a assinatura foi inserida
                ref_node_children = list(ref_node)
                
                # Procura por Signature nos filhos
                signature_found = any('Signature' in str(child.tag) for child in ref_node_children)
                if signature_found:
                    logger.info("SUCESSO: Assinatura encontrada dentro de ref_node!")
                    
            except Exception as e1:
                # TENTATIVA 2: Assinar o root mas referenciar o infDPS
                try:
                    logger.info("Tentativa 2: Assinando root mas referenciando infDPS...")
                    signed_root = signer.sign(
                        root,
                        key=key_data,
                        cert=cert_data,
                        reference_uri="#" + id_infdps
                    )
                    logger.info("Tentativa 2 executada")
                except Exception as e2:
                    logger.error(f"Erro na tentativa 2: {e2}")
                    raise
            
            # Verifica o XML completo após assinatura
            root_xml_apos = etree.tostring(root, encoding='unicode', pretty_print=True)

            # Verifica se há uma assinatura em qualquer lugar
            has_signature = 'Signature' in root_xml_apos or any('Signature' in str(e.tag) for e in root.iter())
            
            if not has_signature:
                # TENTATIVA 3: Usar detached e inserir manualmente
                try:
                    signer_detached = XMLSigner(
                        method=methods.detached,
                        signature_algorithm="rsa-sha256",
                        digest_algorithm="sha256",
                        c14n_algorithm="http://www.w3.org/2001/10/xml-exc-c14n#",
                    )
                    
                    # Assina o ref_node usando detached
                    signature_element = signer_detached.sign(
                        ref_node,
                        key=key_data,
                        cert=cert_data,
                        reference_uri="#" + id_infdps
                    )
                    
                    # Insere a assinatura como filha do root (DPS)
                    root.append(signature_element)
                    
                except Exception as e3:
                    logger.error(f"Erro na tentativa 3 (detached): {e3}")
                    logger.exception(e3)
                
        except Exception as e:
            logger.error(f"Erro ao assinar XML: {e}")
            logger.exception(e)
            raise
        
        # Procura a assinatura criada (normalmente estará dentro de infDPS)
        # Tenta várias formas de busca para garantir que encontra
        signature_node = None
        for search_path in [
            ".//{http://www.w3.org/2000/09/xmldsig#}Signature",
            ".//ds:Signature",
            "Signature",
            "{http://www.w3.org/2000/09/xmldsig#}Signature"
        ]:
            try:
                signature_node = root.find(search_path, namespaces=ns)
                if signature_node is not None:
                    break
            except:
                pass
        
        # Se ainda não encontrou, busca recursivamente
        if signature_node is None:
            for elem in root.iter():
                if elem.tag.endswith('}Signature') or 'Signature' in str(elem.tag):
                    signature_node = elem
                    break
        
        if signature_node is None:
            logger.error("Signature nao encontrada apos assinatura!")
            logger.error(f"XML completo: {etree.tostring(root, encoding='unicode', pretty_print=True)}")
            logger.error(f"Conteudo de ref_node: {etree.tostring(ref_node, encoding='unicode')[:500]}")
            raise ValueError("Assinatura nao foi gerada! Verifique os certificados e tente novamente.")
    
        
        # 3. Move a Signature para FORA de infDPS (como filha de DPS/root) ANTES de processar transforms
        # Isso garante que a assinatura esteja na posição correta conforme o XSD
        parent = signature_node.getparent()
        if parent is not None and parent == ref_node:
            logger.info("Movendo Signature para fora de infDPS...")
            ref_node.remove(signature_node)
            root.append(signature_node)
        
        # 4. Correção das Transforms: Força as 2 Transforms exigidas (Enveloped + Exclusive C14N)
        reference_node = signature_node.find(".//{http://www.w3.org/2000/09/xmldsig#}Reference", namespaces=ns)
        if reference_node is None:
            # Tenta sem namespace
            reference_node = signature_node.find(".//Reference")
        
        if reference_node is None:
            raise ValueError("Reference node nao encontrado na assinatura!")
        
        transforms_node = reference_node.find(".//{http://www.w3.org/2000/09/xmldsig#}Transforms", namespaces=ns)
        if transforms_node is None:
            transforms_node = reference_node.find(".//Transforms")
        
        if transforms_node is None:
            raise ValueError("Transforms node nao encontrado na assinatura!")
        
        # Limpa Transforms existentes
        for transform in list(transforms_node):
             transforms_node.remove(transform)
        
        # Adiciona a 1ª Transform: Enveloped Signature
        enveloped_transform = etree.Element(etree.QName(ns['ds'], "Transform"), 
                                          Algorithm="http://www.w3.org/2000/09/xmldsig#enveloped-signature")
        transforms_node.append(enveloped_transform)
        
        # Adiciona a 2ª Transform: Exclusive C14N
        c14n_exclusive_transform = etree.Element(etree.QName(ns['ds'], "Transform"), 
                                         Algorithm="http://www.w3.org/2001/10/xml-exc-c14n#")
        transforms_node.append(c14n_exclusive_transform)
        
        # 5. Limpeza de namespace redundante (opcional, mas seguro)
        if '{http://www.w3.org/2000/09/xmldsig#}ds' in root.attrib:
            root.attrib.pop('{http://www.w3.org/2000/09/xmldsig#}ds', None)

        # Retorna o XML serializado em bytes
        return etree.tostring(root, encoding='UTF-8', xml_declaration=True, pretty_print=False)
    def emitir_nota(self, dados_nfse: DadosNFSe = None):
        try:
            if dados_nfse is None: dados_nfse = DadosNFSe()
            
            logger.info("1. Gerando XML DPS...")
            xml_dps_str = self.gerar_xml_dps(dados_nfse)
            
            logger.info("2. Assinando XML...")
            if not CERT_PEM:
                raise Exception("Certificados nao configurados")
                
            xml_assinado_bytes = self.sign_xml_string(xml_dps_str, CERT_PEM, KEY_PEM)
            
            # Salva para auditoria
            with open("dps_enviado.xml", "wb") as f:
                f.write(xml_assinado_bytes)
            
            logger.info("3. Enviando...")
            xml_b64 = self.gzip_base64_xml(xml_assinado_bytes)
            
            url = 'https://sefin.nfse.gov.br/sefinnacional/nfse'
            
            headers = {"Content-Type": "application/json"}

            r = self.session.post(url, json={"dpsXmlGZipB64": xml_b64}, headers=headers)
            
            print(f"\n--- RESPOSTA API ---\n")
            if r.status_code not in (200, 201):
                print("{Error}", r.json()['erros'][0], end='\n\n')
                return None
            
            else:
                print('{SUCESSO}:', r.text)

            return r.text
            
        except Exception as e:
            logger.error(f"Erro: {e}")
            return str(e)

def criar_dados_teste():
    dados = DadosNFSe()
    dados.numero_dps = '123456789112345'
    dados.serie_dps = "11111"
    dados.servico.cod_nbs = None
    return dados

if __name__ == "__main__":
    dados = criar_dados_teste()
    processador = ProcessadorNFSeNacional()
    processador.emitir_nota(dados)