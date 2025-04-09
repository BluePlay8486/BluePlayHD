import re
import os
import requests
import xml.etree.ElementTree as ET
from collections import defaultdict
from datetime import datetime

# URL do EPG
EPG_URL = "https://github.com/BluePlay8486/BluePlayHD/raw/refs/heads/main/EPG/epg.xml"

# Baixa e corrige o conteúdo do EPG
response = requests.get(EPG_URL)
epg_raw = response.content.decode("utf-8", errors="ignore")

inicio = epg_raw.find("<tv")
fim = epg_raw.rfind("</tv>") + len("</tv>")
epg_corrigido = epg_raw[inicio:fim]

try:
    epg_tree = ET.fromstring(epg_corrigido)
except ET.ParseError as e:
    print(f"Erro ao processar o EPG: {e}")
    exit(1)

# Lê a lista M3U
with open("lista.m3u", "r", encoding="utf-8") as f:
    lines = f.readlines()

# Grupos que serão incluídos
grupos_desejados = [
    "24H SÉRIES", "24H DESENHOS", "FILMES E SÉRIES", "⭐ REALITY BBB 2025", "ABERTOS",
    "DOCUMENTÁRIOS", "BAND", "NOTÍCIAS", "VARIEDADES", "RELIGIOSOS", "INFANTIL",
    "SKY PLAY", "DISCOVERY", "DISNEY+ | HBO MAX", "24H SHOWS", "GLOBOS REGIONAIS",
    "GLOBOS CAPITAIS", "REDE HBO", "RECORD TV", "SBT", "REDE TELECINE"
]

def normalize(txt):
    txt = txt.lower()
    txt = re.sub(r'[áàãâä]', 'a', txt)
    txt = re.sub(r'[éèêë]', 'e', txt)
    txt = re.sub(r'[íìîï]', 'i', txt)
    txt = re.sub(r'[óòõôö]', 'o', txt)
    txt = re.sub(r'[úùûü]', 'u', txt)
    txt = re.sub(r'[ç]', 'c', txt)
    return re.sub(r'[^a-z0-9]', '', txt)

grupos_norm = {normalize(g): g for g in grupos_desejados}
canais_por_grupo = defaultdict(list)

def extrair_grade(epg_channel):
    grade = []
    for prog in epg_tree.findall(".//programme[@channel='%s']" % epg_channel):
        try:
            inicio = datetime.strptime(prog.attrib.get("start", "")[:12], "%Y%m%d%H%M")
            fim = datetime.strptime(prog.attrib.get("stop", "")[:12], "%Y%m%d%H%M")
            titulo = prog.findtext("title", default="").strip()
            grade.append(f"[COLOR orange]{inicio.strftime('%H:%M')} - {fim.strftime('%H:%M')}[/COLOR] {titulo}")
        except:
            continue
    return "\n".join(grade)

i = 0
while i < len(lines):
    if lines[i].startswith("#EXTINF"):
        match = re.search(r'group-title="([^"]+)"', lines[i])
        grupo_raw = match.group(1) if match else "OUTROS"
        grupo = grupos_norm.get(normalize(grupo_raw))
        if grupo:
            nome = re.search(r',(.+)', lines[i]).group(1)
            logo = re.search(r'tvg-logo="([^"]+)"', lines[i])
            logo_url = logo.group(1) if logo else ''
            link = lines[i+1].strip()
            epg_id = re.search(r'tvg-id="([^"]+)"', lines[i])
            epg_channel = epg_id.group(1) if epg_id else nome.lower().replace(" ", "_")
            grade_epg = extrair_grade(epg_channel)

            if not grade_epg:
                print(f"[SEM EPG] {nome}")
                grade_epg = "[COLOR red]Sem programação encontrada[/COLOR]"

            info = f"[COLOR yellow]Programação Completa:[/COLOR]\n{grade_epg}"

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

# Gera o XML final
output_dir = "BluePlay/TV AO VIVO/CANAIS AO VIVO"
os.makedirs(output_dir, exist_ok=True)
output_path = os.path.join(output_dir, "TV AO VIVO.xml")

with open(output_path, "w", encoding="utf-8") as out:
    out.write('<?xml version="1.0" encoding="UTF-8"?>\n<channels>\n')
    for grupo, canais in canais_por_grupo.items():
        canais.sort()
        out.write(f"""<channel>
<name>[B][COLOR white]{grupo}[/COLOR][/B]</name>
<thumbnail>https://raw.githubusercontent.com/BluePlay8486/BluePlayHD/main/icon.png</thumbnail>
<fanart>https://github.com/AnimeSoul8585/BlackPlay-Tv/raw/refs/heads/main/ICONS%20ADDON/fanart.jpg</fanart>
<items>\n""")
        out.write("\n".join(canais))
        out.write("\n</items>\n</channel>\n")
    out.write("</channels>")
