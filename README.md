# M3U8-Downloader
Script em Python para fazer download de arquivos TS a partir da lista de reprodução em arquivo INDEX.M3U8. Suporta criptografia AES 256 e 128.

Como exemplo de seu funcionamento utilize o link para testes como entrada ao executar o script:
```
https://demo.unified-streaming.com/k8s/features/stable/video/tears-of-steel/tears-of-steel.ism/tears-of-steel-audio_eng=64008-video_eng=401000.m3u8
```

# Assuntos estudados nesse projeto
1. Requisições HTTP
2. Manipulação de strings
3. Manipulação de byte array
4. Decriptografia com AES
5. Escrever arquivos binários

# Requisitos
Será necessário instalar os módulos requests e cryptodome, para isso utilize os seguintes comandos no terminal:
```bash
pip install requests
pip install pycrypto
```

# Formato de arquivo M3U8
Para informações sobre o formato do arquivo acesse [Wikipedia](https://en.wikipedia.org/wiki/M3U)

# Explicação de parte do código
```Python
url_index_file = input("Digite a URL do arquivo Index.m3u8: ")
index_file = url_index_file.split("/")[-1]
url = url_index_file.replace("/{0}".format(index_file), "")
```
1. Solicita entrada do usuário para URL do arquivo index M3U8
2. Utilizando a função split() para dividir a string em um array utilizando como delimitador o caracter "/", atribui o valor do último item a variável index_file
3. Utilizando a função replace() remove o nome do arquivo contido em index_file da entrada do usuário e atribui a string resultante à variável url

```Python
IV = b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01'
IV_counter = 1
```

Os parâmetros iniciais do Vetor de Inicialização da cifra AES foram 0x00000000000000000000000000000001 porque este é um padrão quando o IV não é determinado no arquivo index M3U8. O primeiro arquivo utiliza este vetor de inicialização e os demais recebem IV incrementado de 1 (0x00000000000000000000000000000002, 0x00000000000000000000000000000003, etc).
Deve-se atentar se a sequência começa com 0x00000000000000000000000000000001 ou 0x00000000000000000000000000000000.

```Python
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
```
1. Divide o conteúdo do arquivo index M3U8 linha a linha utilizando a função split() com delimitador "\n".
2. Faz uma iteração por todas as linhas do arquivo.
3. Se encontrar nos primeiros 10 caracteres de alguma linha a string "#EXT-X-KEY", obtém as configurações de criptografia e armazena nas variáveis: key_url (URL para download da chave), IV (vetor de inicialização, caso não tenha sido definido utilizará o padrão citado anteriormente), crypt_method (método de criptografia, normalmente AES 128).
4. Para todas as linhas que não começam com o caracter "#" adiciona o nome do arquivo TS a lista de arquivos TS (ts_file_list).

```Python
if crypt_method != "":
    response = requests.get(key_url)
    key = response.content
```
Se o valor da variável crypt_method for diferente de null_string significa que havia dados sobre criptografia no arquivo index M3U8. Neste caso, a variável key_url terá sido atribuída com o valor da URL do arquivo que contém a chave da cifra:
1. Faz uma requisição HTTP GET para a URL da chave.
2. Armazena os dados (byte array) na variável key.

```Python
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
```
            
1. Faz uma iteração para cada item na lista de arquivos TS (ts_file_list).
2. Faz uma requisição HTTP GET para obter o conteúdo do arquivo TS.
3. Caso a variável crypt_method tenha valor diferente de null_string (o que quer dizer que foram encontrados parâmetros de criptografia no arquivo index M3U8), utiliza um objeto AES para decriptografar o byte array recebido com os seguintes parâmetros: key (chave obtida na etapa anterior), AES.MODE_CBC (modo padrão de utilização da cifra AES), IV (vetor de inicialização obtido como parâmetro no arquivo index M3U8 ou seguindo padrão sequencial conforme explicado acima).
4. Caso os 15 bytes mais significativos da variável IV sejam zero consideramos que não houve parâmetro para IV no arquivo index M3U8 e então estamos utilizando o modo sequencial padrão, então a variável IV (byte array) terá seu byte menos significativo incrementado de 1.

```Python
    #salva arquivo
    file = open(ts_file, "wb")
    file.write(content)
    file.close()
```
Devido o conteúdo do arquivo ser binário, utilizamos o parâmetro "wb" para escrever seu conteúdo que nesta etapa do algoritmo já estará decriptografado caso tenha sido identificado parâmetros de criptografia no arquivo index M3U8.
