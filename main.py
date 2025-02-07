#Pandas para o merge dos Json
import pandas as pd
from flask import Flask, render_template, request, jsonify
import json
#Numpy para calcular o valor medio da VMs 
import numpy as np


app = Flask(__name__)

#Obj da vm
class Vm:
    def __init__(self, name, family, ram, vcpu, os, price):
        self.name = name
        self.family = family
        self.ram = ram
        self.vcpu = vcpu
        self.os = os
        self.price = price
    
    def to_dict(self):
        # Converte o objeto para dicionário
        return {
            "armSkuName": self.name,
            "family": self.family,
            "memoryInMB": self.ram,
            "unitPricePerUnit": self.price,
            "numberOfCores": self.vcpu,
            "os": self.os
        }

#panda le os arquivos da pasta API
df1 = pd.read_json("API/price.json")
df2 = pd.read_json("API/rightsizing.json")

# Merge nos dois Json atraves da coluna 'armSkuName'
df_mesclado = pd.merge(df1, df2, on="armSkuName", how="outer")
# Converter para lista de dicionários
data_merge = df_mesclado.to_dict(orient="records")

#Campos obrigatorios
REQUIRED = ["os", "memoryInMB", "memoryInMB", "osDiskSizeInMB", "numberOfCores"]

# Função para verificar se um produto tem todos os campos obrigatórios preenchidos corretamente
def valid_product(product):
    for any in REQUIRED:
        if any not in product or pd.isna(product[any]) or product[any] in ["", None, "NaN"]:
            return False  # Produto inválido se algum campo estiver ausente ou vazio
    return True  # Produto válido se todos os campos estiverem preenchidos

# Lista de produtos válidos
data_merge = [product for product in data_merge if valid_product(product)]

#Funcao para rota, renderiza os arquivos
def get_API(name_archive):
    with open(name_archive, 'r', encoding='utf-8') as archive:
        return json.load(archive)

@app.route('/api/mesclado', methods=['GET'])
def get_merge():
    return jsonify(data_merge)  

@app.route('/api/price', methods=['GET'])
def get_json1():
    data = get_API('API/price.json')
    return jsonify(data)

@app.route('/api/right', methods=['GET'])
def get_json2():
    data = get_API('API/rightsizing.json')
    return jsonify(data)

#Rota raiz
@app.route('/', methods=['GET','POST', ])
def search():
    if request.method == "POST":
        ram = request.form['ram']
        vcpu = request.form['vcpu']
        os = request.form['os']

        vcpu = float(vcpu) if vcpu else None

        # Convertendo 1GB para 1024MB
        ram = float(ram) * 1024 if ram else None 

        #Filtra para as especificações do user
        request_form = [
            any for any in data_merge
            #Passo o valor escrito para low case
            if(not os or any["os"].lower() == os.lower())
            and (vcpu is None or any["numberOfCores"] == vcpu)
            and (ram is None or any["memoryInMB"] == ram)
        ]

        if request_form:
            #Pego a vm de menor valor com a chave unitPricePerUnit
            vm_cheap = min(request_form, key=lambda s: s["unitPricePerUnit"])
            #Calcula o valor medio com o numpy
            avarage_value = np.mean([item["unitPricePerUnit"] for item in request_form])
            #Pega o valor mais proximo da media
            vm_avarage = min(request_form, key=lambda item: abs(item["unitPricePerUnit"] - avarage_value))
            #Pega o valor maximo 
            vm_expensive = max(request_form, key=lambda s: s["unitPricePerUnit"])
            
            #Cria as 3 VMs
            vm_cheap = Vm(
                name= vm_cheap["armSkuName"],
                family= vm_cheap["family"],
                ram = vm_cheap["memoryInMB"] / 1024,
                price = vm_cheap["unitPricePerUnit"],
                vcpu = vm_cheap["numberOfCores"],
                os = vm_cheap["os"]
            )
            vm_medium = Vm(
                name= vm_avarage["armSkuName"],
                family= vm_avarage["family"],
                ram = vm_avarage["memoryInMB"] / 1024,
                price = vm_avarage["unitPricePerUnit"],
                vcpu = vm_avarage["numberOfCores"],
                os = vm_avarage["os"]
            )
            vm_expensive = Vm(
                name= vm_expensive["armSkuName"],
                family= vm_expensive["family"],
                ram = vm_expensive["memoryInMB"] / 1024,
                price = vm_expensive["unitPricePerUnit"],
                vcpu = vm_expensive["numberOfCores"],
                os = vm_expensive["os"]
            )
            return render_template('search.html', title = 'Search', vm_cheap = vm_cheap, vm_medium = vm_medium, vm_expensive = vm_expensive, txt =" Search the Virtual Machines perfect for you")
        else:
            return render_template('search.html', title = 'Search', txt ="Virtual Machines not found !")
    return render_template('search.html', title = 'Search', txt ="Search the Virtual Machines perfect for you")

app.run(debug=True)