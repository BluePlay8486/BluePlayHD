import os
import re
import requests
import xml.etree.ElementTree as ET
from collections import defaultdict
from datetime import datetime

# CONFIGURAÇÕES
M3U_URL = "http://cdn.pthdtv.top:80/get.php?username=630922725&password=280890306&type=m3u_plus&output=mpegts"
EPG_URL = "https://raw.githubusercontent.com/BluePlay8486/BluePlayHD/refs/heads/main/EPG/epg.xml"
GRUPOS_DESEJADOS = [
    "ESPORTES PPV", "ESPORTES", "CAZÉ TV", "COMBATE | UFC", "DISNEY+ | HBO MAX",
    "ESPN", "NBA LEAGUE | NFL", "NOSSO FUTEBOL", "PREMIERE", "SPORTV"
]
OUTPUT_DIR = "BluePlay/TV AO VIVO/ESPORTES"
OUTPUT_FILE = "ESPORTES.xml"

# FUNÇÕES AUXILIARES
def normalize(txt):
    txt = txt.lower()
    txt = re.sub(r'[áàãâä]', 'a', txt)
    txt = re.sub(r'[éèêë]', 'e', txt)
    txt = re.sub(r'[íìîï]', 'i', txt)
    txt = re.sub(r'[óòõôö]', 'o', txt)
    txt = re.sub(r'[úùûü]', 'u', txt)
    txt = re.sub(r'ç', 'c', txt)
    return re.sub(r'[^a-z0-9]', '', txt)

grupos_norm = {normalize(g): g for g in GRUPOS_DESEJADOS}

def obter_epg():
    try:
        response = requests.get(EPG_URL, timeout=10)
        epg_str = response.content.decode("utf-8", errors="ignore")
        inicio = epg_str.find("<tv")
        fim = epg_str.rfind("</tv>") + len("</tv>")
        return ET.fromstring(epg_str[inicio:fim])
    except Exception as e:
        print(f"[ERRO] Não foi possível carregar o EPG: {e}")
        return None

def extrair_grade(epg_channel, epg_tree):
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

# INÍCIO DO SCRIPT
print("[INFO] Baixando lista M3U...")
try:
    resposta = requests.get(M3U_URL, timeout=15)
    m3u_lines = resposta.text.splitlines()
except Exception as e:
    print(f"[ERRO] Não foi possível baixar a M3U: {e}")
    exit(1)

print("[INFO] Carregando EPG...")
epg_tree = obter_epg()
if epg_tree is None:
    exit(1)

print("[INFO] Processando canais...")
canais_por_grupo = defaultdict(list)
i = 0

while i < len(m3u_lines):
    if m3u_lines[i].startswith("#EXTINF"):
        group_match = re.search(r'group-title="([^"]+)"', m3u_lines[i])
        grupo_raw = group_match.group(1) if group_match else "OUTROS"
        grupo = grupos_norm.get(normalize(grupo_raw))

        if grupo:
            nome = re.search(r',(.+)', m3u_lines[i]).group(1).strip()
            logo = re.search(r'tvg-logo="([^"]+)"', m3u_lines[i])
            logo_url = logo.group(1) if logo else ""
            link = m3u_lines[i + 1].strip()
            epg_id = re.search(r'tvg-id="([^"]+)"', m3u_lines[i])
            epg_channel = epg_id.group(1) if epg_id else nome.lower().replace(" ", "_")

            grade_epg = extrair_grade(epg_channel, epg_tree)
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

# GERANDO XML
print(f"[INFO] Gerando XML em: {OUTPUT_DIR}/{OUTPUT_FILE}")
os.makedirs(OUTPUT_DIR, exist_ok=True)
output_path = os.path.join(OUTPUT_DIR, OUTPUT_FILE)

with open(output_path, "w", encoding="utf-8") as out:
    out.write('<?xml version="1.0" encoding="UTF-8"?>\n<channels>\n')
    for grupo, canais in canais_por_grupo.items():
        canais.sort()
        out.write(f"""<channel>
<name>[B][COLOR white]{grupo}[/COLOR][/B]</name>
<thumbnail>https://github.com/BluePlay8486/BluePlayHD/raw/refs/heads/main/Artes%20Addon/ESPORTES.png</thumbnail>
<fanart>https://github.com/AnimeSoul8585/BlackPlay-Tv/raw/refs/heads/main/ICONS%20ADDON/fanart.jpg</fanart>
<items>\n""")
        out.write("\n".join(canais))
        out.write("\n</items>\n</channel>\n")
    out.write("</channels>")

print(f"[SUCESSO] Arquivo XML salvo em: {output_path}")
