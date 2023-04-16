import requests
from Cryptodome.Cipher import AES

url_index_file = input("Digite a URL do arquivo Index.m3u8: ")
index_file = url_index_file.split("/")[-1]
url = url_index_file.replace("/{0}".format(index_file), "")

#parametros iniciais
key_url = ""
IV = b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01'
IV_counter = 1
crypt_method = ""
ts_file_list = []
key = b''

#requisição do arquivo index
response = requests.get("{0}/{1}".format(url, index_file))


index_array = response.content.decode().split("\n")

for item in index_array:
    #obtem dados de criptografia
    if item[:10] == "#EXT-X-KEY":
        key_config = item[11:]
        configs = key_config.split(",")
        for config in configs:
            par_chave_valor = config.split("=")
            chave = par_chave_valor[0]
            valor = par_chave_valor[1]

            match chave:
                case "URI":
                    key_url = "{0}/{1}".format(url, valor).replace("\"", "")
                case "IV":
                    IV = valor.replace("\"", "").encode("utf-8")
                case "METHOD":
                    crypt_method = valor.replace("\"", "")

    #adiciona arquivo TS na lista para download
    if len(item) > 0:
        if item[0] != "#":
            ts_file_list.append(item)

#requisição da chave de criptografia
if crypt_method != "":
    response = requests.get(key_url)
    key = response.content

#download dos arquivos TS
for ts_file in ts_file_list:
    response = requests.get("{0}/{1}".format(url, ts_file))
    content = response.content

    #decriptografa arquivo TS
    if crypt_method != "":
        aes = AES.new(key, AES.MODE_CBC, IV)
        content = aes.decrypt(content)

        #incrementa 1 ao vetor de inicialização da cifra AES
        #caso não tenha sido especificado IV no arquivo index
        if IV[:-1] == (0).to_bytes(15, "big"):
            IV_counter += 1
            IV = IV_counter.to_bytes(16, "big")

    #salva arquivo
    file = open(ts_file, "wb")
    file.write(content)
    file.close()