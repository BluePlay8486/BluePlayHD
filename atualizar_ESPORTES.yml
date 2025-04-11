import os
import re
import yaml
import requests
import xml.etree.ElementTree as ET
from collections import defaultdict
from datetime import datetime

# Grupos permitidos
grupos_desejados = [
    "ESPORTES PPV", "ESPORTES", "CAZÉ TV", "COMBATE | UFC", "DISNEY+ | HBO MAX",
    "ESPN", "NBA LEAGUE | NFL", "NOSSO FUTEBOL", "PREMIERE", "SPORTV"
]

def normalize(txt):
    txt = txt.lower()
    txt = re.sub(r'[áàãâä]', 'a', txt)
    txt = re.sub(r'[éèêë]', 'e', txt)
    txt = re.sub(r'[íìîï]', 'i', txt)
    txt = re.sub(r'[óòõôö]', 'o', txt)
    txt = re.sub(r'[úùûü]', 'u', txt)
    txt = re.sub(r'ç', 'c', txt)
    return re.sub(r'[^a-z0-9]', '', txt)

grupos_norm = {normalize(g): g for g in grupos_desejados}

# EPG online
EPG_URL = "https://raw.githubusercontent.com/BluePlay8486/BluePlayHD/refs/heads/main/EPG/epg.xml"

def obter_epg_corrigido():
    try:
        response = requests.get(EPG_URL, timeout=10)
        epg_str = response.content.decode("utf-8", errors="ignore")
        inicio = epg_str.find("<tv")
        fim = epg_str.rfind("</tv>") + len("</tv>")
        return ET.fromstring(epg_str[inicio:fim])
    except Exception as e:
        print(f"[ERRO] Não foi possível carregar o EPG: {e}")
        return None

epg_tree = obter_epg_corrigido()
if epg_tree is None:
    exit(1)

def extrair_grade(epg_channel):
    grade = []
    hoje = datetime.now().date()
    for prog in epg_tree.findall(f".//programme[@channel='{epg_channel}']"):
        try:
            inicio = datetime.strptime(prog.attrib.get("start", "")[:12], "%Y%m%d%H%M")
            fim = datetime.strptime(prog.attrib.get("stop", "")[:12], "%Y%m%d%H%M")
            if inicio.date() != hoje:
                continue
            titulo = prog.findtext("title", default="").strip()
            horario = f"[COLOR orange]{inicio.strftime('%H:%M')} - {fim.strftime('%H:%M')}[/COLOR]"
            grade.append(f"{horario} {titulo}")
        except:
            continue
    return "\n".join(grade)

# Arquivo de entrada
yaml_file = "Atualizar_TV.AO.VIVO.yml"
output_file = "ESPORTES.txt"

# Lê YAML
try:
    with open(yaml_file, "r", encoding="utf-8") as f:
        canais = yaml.safe_load(f)
except FileNotFoundError:
    print(f"[ERRO] Arquivo '{yaml_file}' não encontrado.")
    exit(1)

canais_por_grupo = defaultdict(list)

for canal in canais:
    nome = canal.get("nome", "Sem Nome")
    link = canal.get("link", "")
    logo = canal.get("logo", "")
    grupo_raw = canal.get("grupo", "OUTROS")
    grupo = grupos_norm.get(normalize(grupo_raw))
    if not grupo:
        continue

    epg_id = canal.get("epg", nome.lower().replace(" ", "_"))
    grade_epg = extrair_grade(epg_id)
    if not grade_epg:
        print(f"[SEM EPG] {nome}")
        grade_epg = "[COLOR red]Sem programação encontrada[/COLOR]"

    info = f"[COLOR yellow]Programação Completa:[/COLOR]\n{grade_epg}"

    item = f"""<item>
<title>{nome}</title>
<link>{link}</link>
<thumbnail>{logo}</thumbnail>
<fanart>https://github.com/AnimeSoul8585/BlackPlay-Tv/raw/refs/heads/main/ICONS%20ADDON/fanart.jpg</fanart>
<info>{info}</info>
</item>"""

    canais_por_grupo[grupo].append(item)

# Gera o XML personalizado
with open(output_file, "w", encoding="utf-8") as out:
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

print(f"[SUCESSO] Arquivo gerado: {output_file}")
