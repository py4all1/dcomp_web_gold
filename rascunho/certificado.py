
from os import listdir
from cryptography.hazmat.primitives.serialization import Encoding, PrivateFormat, NoEncryption
from cryptography.hazmat.primitives.serialization.pkcs12 import load_key_and_certificates

root_cert = "./"

def listar_certificados():
    certs = root_cert
    fcerts = []

    for file in listdir(certs):
        if file[-4:] == '.pfx':
            fcerts.append(file)
    
    return fcerts
def extrair_key_and_pem(pfx_path: str, password: str):
    # caminho e senha do .pfx
    pfx_path = root_cert + pfx_path
    pfx_password = password.encode()  # se não tiver senha, use: None

    # ler o conteúdo binário do pfx
    with open(pfx_path, "rb") as f:
        pfx_data = f.read()

    # carregar chave, certificado e cadeia intermediária
    private_key, certificate, additional_certs = load_key_and_certificates(pfx_data, pfx_password)

    # salvar o certificado
    with open(root_cert + "client_cert.pem", "wb") as f:
        f.write(certificate.public_bytes(Encoding.PEM))

    # salvar a chave privada
    with open(root_cert + "client_key.pem", "wb") as f:
        f.write(private_key.private_bytes(
            encoding=Encoding.PEM,
            format=PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=NoEncryption()
        ))

    return True

