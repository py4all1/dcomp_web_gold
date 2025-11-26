"""
Serviço de Certificado Digital para Django
Gerencia conversão PFX para PEM e operações com certificados
"""
import os
from django.conf import settings
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.serialization import (
    Encoding,
    PrivateFormat,
    NoEncryption,
)
from cryptography.hazmat.primitives.serialization.pkcs12 import load_key_and_certificates


class CertificadoService:
    """
    Serviço para gerenciar certificados digitais no Django
    """
    
    def __init__(self):
        self.cert_dir = os.path.join(settings.BASE_DIR, 'certificados')
        os.makedirs(self.cert_dir, exist_ok=True)
    
    def converter_pfx_para_pem(self, empresa):
        """
        Converte certificado PFX para PEM
        
        Args:
            empresa: Instância do modelo Empresa
            
        Returns:
            str: Caminho do arquivo PEM gerado
        """
        # Caminhos dos arquivos
        cnpj_limpo = empresa.cnpj.replace('.', '').replace('/', '').replace('-', '')
        
        # Tenta encontrar o certificado em múltiplos locais
        # 1. Pasta certificados no BASE_DIR (produção e desenvolvimento)
        pfx_path = os.path.join(settings.BASE_DIR, 'certificados', empresa.certificado_arquivo)
        
        # 2. Se não encontrar, tenta em MEDIA_ROOT/certificados
        if not os.path.exists(pfx_path):
            pfx_path = os.path.join(settings.MEDIA_ROOT, 'certificados', empresa.certificado_arquivo)
        
        pem_path = os.path.join(self.cert_dir, f"{cnpj_limpo}.pem")
        
        # Se PEM já existe, retorna
        if os.path.exists(pem_path):
            return pem_path
        
        # Verifica se o arquivo PFX existe
        if not os.path.exists(pfx_path):
            raise FileNotFoundError(f"Certificado PFX não encontrado: {pfx_path}")
        
        # Lê o arquivo PFX
        with open(pfx_path, "rb") as pfx_file:
            pfx_data = pfx_file.read()
        
        # Senha do certificado
        password = empresa.senha_certificado.encode("utf-8") if empresa.senha_certificado else None
        
        # Carrega chave e certificados
        try:
            key, cert, ca = load_key_and_certificates(
                pfx_data, password, default_backend()
            )
        except Exception as e:
            raise Exception(f"Erro ao carregar certificado PFX: {str(e)}")
        
        # Salva em formato PEM
        with open(pem_path, "wb") as pem_file:
            # Chave privada
            pem_file.write(
                key.private_bytes(
                    encoding=Encoding.PEM,
                    format=PrivateFormat.TraditionalOpenSSL,
                    encryption_algorithm=NoEncryption(),
                )
            )
            
            # Certificado
            pem_file.write(cert.public_bytes(encoding=Encoding.PEM))
            
            # Certificados adicionais (cadeia)
            if ca:
                for cert_adicional in ca:
                    pem_file.write(cert_adicional.public_bytes(encoding=Encoding.PEM))
        
        return pem_path
    
    def get_pem_path(self, empresa):
        """
        Retorna o caminho do certificado PEM, convertendo se necessário
        
        Args:
            empresa: Instância do modelo Empresa
            
        Returns:
            str: Caminho do arquivo PEM
        """
        cnpj_limpo = empresa.cnpj.replace('.', '').replace('/', '').replace('-', '')
        pem_path = os.path.join(self.cert_dir, f"{cnpj_limpo}.pem")
        
        if not os.path.exists(pem_path):
            return self.converter_pfx_para_pem(empresa)
        
        return pem_path
