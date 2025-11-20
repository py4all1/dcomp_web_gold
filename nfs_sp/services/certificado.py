# -*- coding: utf-8 -*-
# openssl genrsa -out chave-privada.pem 2048
# openssl rsa -in chave-privada.pem -out chave-publica.pem -outform PEM -pubout
# openssl req -new -x509 -key chave-privada.pem -out certificado.pem -days 365


from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.serialization import (
    Encoding,
    PrivateFormat,
    NoEncryption,
)
from cryptography.hazmat.primitives.serialization.pkcs12 import (
    load_key_and_certificates,
)
from cryptography.hazmat.primitives.serialization import pkcs12
from Entidades import Entidade
from OpenSSL import crypto
import tempfile
import os
from cryptography import x509
from cryptography.hazmat.backends import default_backend

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.x509 import Certificate
import subprocess




class Certificado(Entidade):
    """Classe abstrata responsavel por definir o modelo padrao para as demais
    classes de certificados digitais.

    Caso va implementar um novo formato de certificado, crie uma classe que
    herde desta."""

    def __new__(cls, *args, **kwargs):
        if cls == Certificado:
            raise Exception("Esta classe nao pode ser instanciada diretamente!")
        else:
            return super(Certificado, cls).__new__(cls)


class CertificadoA1(Certificado):
    """Implementa a entidade do certificado eCNPJ A1, suportado pelo OpenSSL,
    e amplamente utilizado."""

    caminho_arquivo = None

    def __init__(self, caminho_arquivo=None):
        self.caminho_arquivo = caminho_arquivo
        self.arquivos_temp = []

    def separar_arquivo(self, senha, caminho=False):
        """Separa o arquivo de certificado em dois: de chave e de certificado,
        e retorna a string. Se caminho for True grava na pasta temporaria e retorna
        o caminho dos arquivos, senao retorna o objeto. Apos o uso devem ser excluidos com o metodo excluir.
        """

        try:
            with open(self.caminho_arquivo, "rb") as cert_arquivo:
                cert_conteudo = cert_arquivo.read()
        except (PermissionError, FileNotFoundError) as exc:
            raise Exception(
                "Falha ao abrir arquivo do certificado digital A1. Verifique local e permissoes do arquivo."
            ) from exc
        except Exception as exc:
            raise Exception(
                "Falha ao abrir arquivo do certificado digital A1. Causa desconhecida."
            ) from exc

        # Carrega o arquivo .pfx, erro pode ocorrer se a senha estiver errada ou formato invalido.
        try:
            pkcs12 = crypto.load_pkcs12(cert_conteudo, senha)
        except crypto.Error as exc:
            raise Exception(
                "Falha ao carregar certificado digital A1. Verifique a senha do certificado."
            ) from exc
        except Exception as exc:
            raise Exception(
                "Falha ao carregar certificado digital A1. Causa desconhecida."
            ) from exc

        if caminho:
            cert = crypto.dump_certificate(
                crypto.FILETYPE_PEM, pkcs12.get_certificate()
            )
            chave = crypto.dump_privatekey(crypto.FILETYPE_PEM, pkcs12.get_privatekey())
            # cria arquivos temporarios
            with tempfile.NamedTemporaryFile(delete=False) as arqcert:
                arqcert.write(cert)
            with tempfile.NamedTemporaryFile(delete=False) as arqchave:
                arqchave.write(chave)
            self.arquivos_temp.append(arqchave.name)
            self.arquivos_temp.append(arqcert.name)
            return arqchave.name, arqcert.name
        else:
            # Certificado
            cert = crypto.dump_certificate(
                crypto.FILETYPE_PEM, pkcs12.get_certificate()
            ).decode("utf-8")
            cert = cert.replace("\n", "")
            cert = cert.replace("\t", "")
            cert = cert.replace("-----BEGIN CERTIFICATE-----", "")
            cert = cert.replace("-----END CERTIFICATE-----", "")

            # Chave, string decodificada da chave privada
            chave = crypto.dump_privatekey(crypto.FILETYPE_PEM, pkcs12.get_privatekey())
            # with open('CHAVEBIOC', "wb") as f:
            #     f.write(chave)
            # with open('CERTBIOC', "w") as f:
            #     f.write(cert)
            return chave, cert

    def excluir(self):
        """Exclui os arquivos temporarios utilizados para o request."""
        try:
            for i in self.arquivos_temp:
                os.remove(i)
            self.arquivos_temp.clear()
        except:
            pass

    def converter_pfx_para_pem(self, caminho_pfx, senha):
        caminho_pem = os.path.splitext(caminho_pfx)[0] + ".pem"

        try:
            comando = f"openssl pkcs12 -in {caminho_pfx} -out {caminho_pem} -nodes -password pass:{senha}"
            subprocess.run(comando, shell=True, check=True)
        except subprocess.CalledProcessError as e:
            # MsgBox('OK',"Erro ao converter o certificado PFX para PEM:", e)
            # MsgBox('OK',f'caminho_pfx {caminho_pfx} ', f'{caminho_pem} caminho_pem')

            return None

        return caminho_pem

    def convert_pfx_to_pem(self, pfx_path, pem_path, password):
        caminho_pem = os.path.splitext(pfx_path)[0] + ".pem"
        with open(pfx_path, "rb") as pfx_file:
            pfx_data = pfx_file.read()

        key, cert, ca = load_key_and_certificates(
            pfx_data, password.encode("utf-8"), default_backend()
        )

        # Salva a chave privada em um arquivo PEM
        with open(pem_path, "wb") as pem_file:
            pem_file.write(
                key.private_bytes(
                    encoding=Encoding.PEM,
                    format=PrivateFormat.TraditionalOpenSSL,
                    encryption_algorithm=NoEncryption(),
                )
            )

            # Salva o certificado em um arquivo PEM
            pem_file.write(cert.public_bytes(encoding=Encoding.PEM))
            for cert in ca:
                pem_file.write(cert.public_bytes(encoding=Encoding.PEM))

        return caminho_pem

    def pegar_validade(self, senha, caminho=False):
        try:
            # Se um caminho for fornecido, usa-o, caso contrário, usa o caminho padrão armazenado na instância.
            caminho_certificado = caminho if caminho else self.caminho_arquivo

            # Lê o conteúdo do arquivo .pfx
            with open(caminho_certificado, "rb") as cert_arquivo:
                cert_conteudo = cert_arquivo.read()
        except (PermissionError, FileNotFoundError) as exc:
            raise Exception(
                "Falha ao abrir arquivo do certificado digital A1. Verifique local e permissões do arquivo."
            ) from exc
        except Exception as exc:
            raise Exception(
                "Falha ao abrir arquivo do certificado digital A1. Causa desconhecida."
            ) from exc

        # Carrega o arquivo .pfx usando cryptography
        try:
            key, cert, additional_certs = pkcs12.load_key_and_certificates(
                cert_conteudo, senha.encode(), default_backend()
            )
        except ValueError as exc:
            raise Exception(
                "Falha ao carregar certificado digital A1. Verifique a senha ou o formato do certificado."
            ) from exc
        except Exception as exc:
            print(f"Erro desconhecido na linha: {exc.__traceback__.tb_lineno} - certificado.py: {exc}")
            raise Exception(
                "Falha ao carregar certificado digital A1. Causa desconhecida."
            ) from exc

        # Obtém a validade do certificado (data de expiração)
        if isinstance(cert, Certificate):
            validade = cert.not_valid_after
            validade_formatada = validade.strftime("%d/%m/%Y")
            return validade_formatada
        else:
            raise Exception("Certificado não encontrado ou inválido.")
        

if __name__ == "__main__":
    cer = CertificadoA1("Certificados\\13560469000127.pfx")
    aa = cer.separar_arquivo('1234', True)
    print(aa)
    # Caminho para o certificado .pfx
    # Caminho para o certificado PFX
    pfx_path = 'Certificados\\29797601000159.pfx'

    # # Senha para o certificado PFX
    # password = '123456'  # Substitua pela senha real

    # # Caminho para o certificado PEM
    pem_path = '29797601000159.pem'

    # # Converte o .pfx para .pem
    cer.convert_pfx_to_pem(pfx_path, pem_path, '123456')
