import re
import os
import xml.etree.ElementTree as ET
from collections import defaultdict

# Lê o arquivo M3U
with open("lista.m3u", "r", encoding="utf-8") as f:
    lines = f.readlines()

# Lê o EPG XML
epg_url = "EPG/epg.xml"
epg_data = {}
if os.path.exists(epg_url):
    tree = ET.parse(epg_url)
    root = tree.getroot()
    for prog in root.findall("programme"):
        channel = prog.attrib.get("channel")
        start = prog.attrib.get("start", "")[:12]
        title = prog.findtext("title", default="Sem título")
        if channel not in epg_data:
            epg_data[channel] = []
        epg_data[channel].append(f"{start[:2]}:{start[2:4]} - {title}")

# Grupos desejados
grupos_desejados = [
    "24H SÉRIES", "24H DESENHOS", "FILMES E SÉRIES", "⭐ REALITY BBB 2025", "ABERTOS",
    "DOCUMENTÁRIOS", "BAND", "NOTÍCIAS", "VARIEDADES", "RELIGIOSOS", "INFANTIL",
    "SKY PLAY", "DISCOVERY", "DISNEY+ | HBO MAX", "24H SHOWS", "GLOBOS REGIONAIS",
    "GLOBOS CAPITAIS", "REDE HBO", "RECORD TV", "SBT", "REDE TELECINE"
]

# Função para normalizar os nomes
def normalize(txt):
    txt = txt.lower()
    txt = re.sub(r'[áàãâä]', 'a', txt)
    txt = re.sub(r'[éèêë]', 'e', txt)
    txt = re.sub(r'[íìîï]', 'i', txt)
    txt = re.sub(r'[óòõôö]', 'o', txt)
    txt = re.sub(r'[úùûü]', 'u', txt)
    txt = re.sub(r'[ç]', 'c', txt)
    return re.sub(r'[^a-z0-9]', '', txt)

# Mapeamento dos grupos normalizados
grupos_norm = {normalize(g): g for g in grupos_desejados}
canais_por_grupo = defaultdict(list)

# Processamento da lista M3U
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

            # Monta a info com programação do EPG
            if epg_channel in epg_data:
                prog_info = "\n".join(epg_data[epg_channel][:10])  # Limita a 10 entradas
                info = f"[COLOR yellow]Programação:[/COLOR]\n{prog_info}"
                print(f"[EPG OK] Canal: {nome}")
            else:
                info = "[COLOR yellow]Programação não encontrada.[/COLOR]"
                print(f"[SEM EPG] Canal: {nome}")

            item = f"""<item>
<title>{nome}</title>
<link>{link}</link>
<thumbnail>{logo_url}</thumbnail>
<fanart>https://github.com/AnimeSoul8585/BlackPlay-Tv/raw/refs/heads/main/ICONS%20ADDON/fanart.jpg</fanart>
<info>{info}</info>
<epg_url>https://github.com/BluePlay8486/BluePlayHD/raw/refs/heads/main/EPG/epg.xml</epg_url>
<epg_regex>&lt;programme.*?channel="{epg_channel}".*?start="(.*?)".*?stop="(.*?)".*?&gt;.*?&lt;title.*?&gt;(.*?)&lt;/title&gt;</epg_regex>
</item>"""
            canais_por_grupo[grupo].append(item)
        i += 2
    else:
        i += 1

# Garante que o diretório existe
output_dir = "BluePlay/TV AO VIVO/CANAIS AO VIVO"
os.makedirs(output_dir, exist_ok=True)

# Caminho final do arquivo XML
output_path = os.path.join(output_dir, "TV AO VIVO.xml")

# Escrita do XML
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
