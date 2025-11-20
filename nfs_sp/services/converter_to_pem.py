import os
import subprocess
from cryptography.hazmat.primitives import serialization


def converter_pfx_para_pem(caminho_pfx, senha):
    caminho_pem = os.path.splitext(caminho_pfx)[0] + ".pem"

    try:
        comando = f"openssl pkcs12 -in {caminho_pfx} -out {caminho_pem} -nodes -password pass:{senha}"
        subprocess.run(comando, shell=True, check=True)
    except subprocess.CalledProcessError as e:
        print("Erro ao converter o certificado PFX para PEM:", e)
        return None

    return caminho_pem


# Exemplo de uso:
caminho_pfx = "Certificados/ENJOY_Matriz.pfx"
senha_pfx = "123456"
caminho_pem = converter_pfx_para_pem(caminho_pfx, senha_pfx)

if caminho_pem:
    # Faça algo com o caminho do arquivo PEM gerado
    print("Arquivo PEM gerado:", caminho_pem)
else:
    # Trate o erro ou exiba uma mensagem de falha
    print("Falha ao converter o certificado PFX para PEM.")
