import re
import os
import requests
import xml.etree.ElementTree as ET
from collections import defaultdict
from datetime import datetime

EPG_URL = "https://raw.githubusercontent.com/BluePlay8486/BluePlayHD/refs/heads/main/EPG/epg.xml"
M3U_URL = "http://cdn.pthdtv.top:80/get.php?username=630922725&password=280890306&type=m3u_plus&output=mpegts"
EPG_REGEX = r"(?<=\])[^:\n]+(?=\s\-|\<|\\n|\\)"  # Adicionado aqui

# Normaliza nomes para facilitar o agrupamento
def normalize(txt):
    txt = txt.lower()
    txt = re.sub(r'[áàãâä]', 'a', txt)
    txt = re.sub(r'[éèêë]', 'e', txt)
    txt = re.sub(r'[íìîï]', 'i', txt)
    txt = re.sub(r'[óòõôö]', 'o', txt)
    txt = re.sub(r'[úùûü]', 'u', txt)
    txt = re.sub(r'ç', 'c', txt)
    return re.sub(r'[^a-z0-9]', '', txt)

# Lista ordenada dos grupos aceitos
grupos_desejados = [
    "LANÇAMENTOS 2025", "LANÇAMENTOS 2024", "LANÇAMENTOS 2023", "LANÇAMENTOS 2022",
    "FILMES | LEGENDADOS", "FILMES DRAMA", "FILMES ROMANCE", "FILMES TERROR",
    "FILMES AÇÃO", "FILMES FICÇÃO", "FILMES AVENTURA", "FILMES FANTASIA", "FILMES | 4K",
    "FILMES SUSPENSE", "FILMES NACIONAL", "FILMES GUERRA", "FILMES PRIME VIDEO",
    "FILMES ANIMAÇÃO", "FILMES COMÉDIA", "FILMES DOCUMENTÁRIOS", "FILMES FAROESTE",
    "FILMES NETFLIX", "FILMES INFANTIL", "FILMES ANIME", "FILMES DISNEY+", "FILMES APPLE TV+",
    "FILMES GLOBOPLAY", "FILMES PARAMOUNT+", "FILMES HBO MAX", "FILMES STAR+", "FILMES CRIME",
    "FILMES | COPA DO MUNDO 2022", "FILMES RELIGIOSOS", "FILMES BRASIL PARALELO",
    "FILMES | DESPERTAR UMA NOVA CONSCIÊNCIA", "FILMES | SONS PARA DORMIR",
    "FILMES DC COMICS", "FILMES MARVEL", "FILMES | 007 COLEÇÃO"
]

grupos_norm = {normalize(g): g for g in grupos_desejados}
canais_por_grupo = defaultdict(list)

# EPG
def obter_epg():
    try:
        r = requests.get(EPG_URL, timeout=10)
        conteudo = r.content.decode("utf-8", errors="ignore")
        inicio = conteudo.find("<tv")
        fim = conteudo.rfind("</tv>") + len("</tv>")
        return ET.fromstring(conteudo[inicio:fim])
    except Exception as e:
        print(f"[ERRO] Falha ao carregar EPG: {e}")
        return None

epg_tree = obter_epg()
if epg_tree is None:
    exit(1)

def extrair_grade(epg_channel):
    grade = []
    for prog in epg_tree.findall(f'.//programme[@channel="{epg_channel}"]'):
        titulo = prog.findtext('title') or 'Sem título'
        inicio = prog.get('start')
        fim = prog.get('stop')
        if inicio and fim:
            try:
                inicio_fmt = datetime.strptime(inicio[:14], "%Y%m%d%H%M%S").strftime("%d/%m %H:%M")
                fim_fmt = datetime.strptime(fim[:14], "%Y%m%d%H%M%S").strftime("%H:%M")
                grade.append(f"[B]{inicio_fmt} às {fim_fmt}:[/B] {titulo}")
            except:
                continue
    return "\n".join(grade)

# Baixa e interpreta a M3U
try:
    response = requests.get(M3U_URL, timeout=10)
    linhas = response.text.splitlines()
except Exception as e:
    print(f"[ERRO] Falha ao baixar M3U: {e}")
    exit(1)

i = 0
while i < len(linhas):
    if linhas[i].startswith("#EXTINF"):
        grupo_match = re.search(r'group-title="([^"]+)"', linhas[i])
        grupo_raw = grupo_match.group(1) if grupo_match else "OUTROS"
        grupo = grupos_norm.get(normalize(grupo_raw))

        if grupo:
            nome = re.search(r',(.+)', linhas[i])
            nome = nome.group(1).strip() if nome else "Sem nome"
            logo = re.search(r'tvg-logo="([^"]+)"', linhas[i])
            logo_url = logo.group(1).strip() if logo else ""
            if not logo_url.startswith("http"):
                logo_url = ""
            epg_id = re.search(r'tvg-id="([^"]+)"', linhas[i])
            epg_channel = epg_id.group(1) if epg_id else normalize(nome)
            link = linhas[i + 1].strip() if i + 1 < len(linhas) else ""

            grade = extrair_grade(epg_channel)
            if not grade:
                grade = "[COLOR red]Sem programação encontrada[/COLOR]"

            info = f"[COLOR yellow]Programação Completa:[/COLOR]\n{grade}"

            item = f"""<item>
<title>{nome}</title>
<link>{link}</link>
<thumbnail>{logo_url}</thumbnail>
<fanart>https://github.com/AnimeSoul8585/BlackPlay-Tv/raw/refs/heads/main/ICONS%20ADDON/fanart.jpg</fanart>
<info>{info}</info>
</item>"""

            canais_por_grupo[grupo].append(item)
        i += 2
    else:
        i += 1

# Escreve o XML
output_path = "BluePlay/FILMES/LINK DIRETO/FILMES.txt"
os.makedirs(os.path.dirname(output_path), exist_ok=True)

with open(output_path, "w", encoding="utf-8") as f:
    f.write('<?xml version="1.0" encoding="UTF-8"?>\n<channels>\n')
    for grupo in grupos_desejados:
        canais = canais_por_grupo.get(grupo)
        if not canais:
            continue
        f.write(f"""<channel>
<name>[B][COLOR white]{grupo}[/COLOR][/B]</name>
<thumbnail>https://raw.githubusercontent.com/BluePlay8486/BluePlayHD/main/icon.png</thumbnail>
<fanart>https://github.com/AnimeSoul8585/BlackPlay-Tv/raw/refs/heads/main/ICONS%20ADDON/fanart.jpg</fanart>
<epg_url>{EPG_URL}</epg_url>
<epg_regex>{EPG_REGEX}</epg_regex>
<items>\n""")
        f.write("\n".join(sorted(canais)))
        f.write("\n</items>\n</channel>\n")
    f.write("</channels>")

print(f"[SUCESSO] Arquivo gerado em: {output_path}")
