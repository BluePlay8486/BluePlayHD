import requests
import xml.etree.ElementTree as ET
from collections import defaultdict

# URL da lista M3U
m3u_url = "URL_DA_SUA_LISTA_M3U_AQUI"

# Caminho para salvar o XML no estilo do BluePlay
output_file = "BluePlay/FILMES/LINK DIRETO/FILMES.txt"

# Grupos de filmes em ordem específica
ordem_grupos = [
    "LANÇAMENTOS 2025", "LANÇAMENTOS 2024", "LANÇAMENTOS 2023", "LANÇAMENTOS 2022",
    "FILMES | LEGENDADOS", "FILMES DRAMA", "FILMES ROMANCE", "FILMES TERROR", 
    "FILMES AÇÃO", "FILMES FICÇÃO", "FILMES AVENTURA", "FILMES FANTASIA", 
    "FILMES | 4K", "FILMES SUSPENSE", "FILMES NACIONAL", "FILMES GUERRA", 
    "FILMES PRIME VIDEO", "FILMES ANIMAÇÃO", "FILMES COMÉDIA", "FILMES DOCUMENTÁRIOS", 
    "FILMES FAROESTE", "FILMES NETFLIX", "FILMES INFANTIL", "FILMES ANIME", 
    "FILMES DISNEY+", "FILMES APPLE TV+", "FILMES GLOBOPLAY", "FILMES PARAMOUNT+", 
    "FILMES HBO MAX", "FILMES STAR+", "FILMES CRIME", "FILMES | COPA DO MUNDO 2022", 
    "FILMES RELIGIOSOS", "FILMES BRASIL PARALELO", "FILMES | DESPERTAR UMA NOVA CONSCIÊNCIA", 
    "FILMES | SONS PARA DORMIR", "FILMES DC COMICS", "FILMES MARVEL", "FILMES | 007 COLEÇÃO"
]

# Baixar lista M3U
response = requests.get(m3u_url)
lines = response.text.splitlines()

# Agrupar canais por grupo
canais_por_grupo = defaultdict(list)
for i in range(len(lines)):
    if lines[i].startswith('#EXTINF'):
        info = lines[i]
        link = lines[i + 1]
        tvg_name = info.split('tvg-name="')[1].split('"')[0] if 'tvg-name="' in info else "Sem Nome"
        tvg_logo = info.split('tvg-logo="')[1].split('"')[0] if 'tvg-logo="' in info else ""
        group = info.split('group-title="')[1].split('"')[0] if 'group-title="' in info else "OUTROS"

        if group in ordem_grupos:
            canais_por_grupo[group].append({
                "name": tvg_name,
                "logo": tvg_logo,
                "link": link
            })

# Criar XML no estilo BluePlay
xml_content = '<?xml version="1.0" encoding="UTF-8"?>\n<rss>\n'
for grupo in ordem_grupos:
    canais = canais_por_grupo.get(grupo, [])
    if canais:
        xml_content += f'  <channel>\n    <title>[COLOR orange][B]{grupo}[/B][/COLOR]</title>\n'
        for canal in canais:
            xml_content += f'''    <item>
      <title>[COLOR white][B]{canal["name"]}[/B][/COLOR]</title>
      <link>{canal["link"]}</link>
      <info>[COLOR yellow]Filme:[/COLOR] {canal["name"]}</info>
      <thumbnail>{canal["logo"]}</thumbnail>
      <fanart>{canal["logo"]}</fanart>
    </item>\n'''
        xml_content += '  </channel>\n'

xml_content += '</rss>'

# Salvar arquivo
with open(output_file, "w", encoding="utf-8") as f:
    f.write(xml_content)

print(f"Arquivo {output_file} gerado com sucesso!")
