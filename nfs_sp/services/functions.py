import requests
import json
import time


def consulta_cnpj(CNPJId):
    url = f"https://www.receitaws.com.br/v1/cnpj/{CNPJId}"

    querystring = {
        "token": "XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX",
        "cnpj": "06990590000123",
        "plugin": "RF",
    }

    response = requests.request("GET", url, params=querystring)
    if response.status_code == 429:
        time.sleep(42)
        return 429

    resp = json.loads(response.text)

    print(resp)

    return (
        resp["nome"],
        resp["logradouro"],
        resp["numero"],
        resp["complemento"],
        resp["bairro"],
        resp["municipio"],
        resp["uf"],
        resp["cep"],
        resp["telefone"],
        resp["email"],
    )