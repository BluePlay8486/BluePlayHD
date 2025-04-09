import re
import os
import requests
import xml.etree.ElementTree as ET
from collections import defaultdict
from datetime import datetime

# Lê o arquivo M3U
with open("lista.m3u", "r", encoding="utf-8") as f:
    lines = f.readlines()

# Baixa o EPG e extrai apenas <programme>
epg_url = "https://github.com/BluePlay8486/BluePlayHD/raw/refs/heads/main/EPG/epg.xml"
epg_raw = requests.get(epg_url).text

# Extrai somente as tags <programme>
programmes_xml = "<tv>" + "\n".join(re.findall(r"<programme .*?</programme>", epg_raw, flags=re.DOTALL)) + "</tv>"
epg_tree = ET.fromstring(programmes_xml)

# Lista de grupos desejados
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

def programa_atual(epg_channel):
    agora = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    for prog in epg_tree.findall("programme"):
        canal = prog.attrib.get("channel", "").lower()
        inicio = prog.attrib.get("start", "")[:14]
        fim = prog.attrib.get("stop", "")[:14]
        if canal == epg_channel.lower() and inicio <= agora <= fim:
            titulo = prog.findtext("title", default="Sem título")
            return f"[COLOR yellow]Agora:[/COLOR] {titulo} ({inicio[8:10]}:{inicio[10:12]} - {fim[8:10]}:{fim[10:12]})"
    return "[COLOR yellow]Canal ao vivo com programação atualizada.[/COLOR]"

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
            link = lines[i + 1].strip()

            epg_id = re.search(r'tvg-id="([^"]+)"', lines[i])
            epg_channel = epg_id.group(1) if epg_id else nome.lower().replace(" ", "_")

            info_text = programa_atual(epg_channel)

            item = f"""<item>
<title>{nome}</title>
<link>{link}</link>
<thumbnail>{logo_url}</thumbnail>
<fanart>https://github.com/AnimeSoul8585/BlackPlay-Tv/raw/refs/heads/main/ICONS%20ADDON/fanart.jpg</fanart>
<info>{info_text}</info>
<epg_url>{epg_url}</epg_url>
<epg_regex>&lt;programme.*?channel="{epg_channel}".*?start="(.*?)".*?stop="(.*?)".*?&gt;.*?&lt;title.*?&gt;(.*?)&lt;/title&gt;</epg_regex>
</item>"""
            canais_por_grupo[grupo].append(item)
        i += 2
    else:
        i += 1

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
