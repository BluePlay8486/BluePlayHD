import re
import os
import requests
import xml.etree.ElementTree as ET
from collections import defaultdict
from datetime import datetime
import emoji

# URL do EPG e M3U
EPG_URL = "https://raw.githubusercontent.com/BluePlay8486/BluePlayHD/main/EPG/epg.xml"
M3U_URL = "http://cdn.pthdtv.top:80/get.php?username=630922725&password=280890306&type=m3u_plus&output=mpegts"

# Grupos desejados
grupos_desejados = [
    "LANÇAMENTOS 2025", "LANÇAMENTOS 2024", "LANÇAMENTOS 2023", "LANÇAMENTOS 2022",
    "FILMES | LEGENDADOS", "FILMES DRAMA", "FILMES ROMANCE", "FILMES TERROR",
    "FILMES AÇÃO", "FILMES FICÇÃO", "FILMES AVENTURA", "FILMES FANTASIA",
    "FILMES | 4K", "FILMES SUSPENSE", "FILMES NACIONAL", "FILMES GUERRA",
    "FILMES PRIME VIDEO", "FILMES ANIMAÇÃO", "FILMES COMÉDIA", "FILMES DOCUMENTÁRIOS",
    "FILMES FAROESTE", "FILMES NETFLIX", "FILMES INFANTIL", "FILMES ANIME",
    "FILMES DISNEY+", "FILMES APPLE TV+", "FILMES GLOBOPLAY", "FILMES PARAMOUNT+",
    "FILMES HBO MAX", "FILMES STAR+", "FILMES CRIME", "FILMES | COPA DO MUNDO 2022",
    "FILMES RELIGIOSOS", "FILMES BRASIL PARALELO",
    "FILMES | DESPERTAR UMA NOVA CONSCIÊNCIA", "FILMES | SONS PARA DORMIR",
    "FILMES DC COMICS", "FILMES MARVEL", "FILMES | 007 COLEÇÃO"
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

def limpar_texto(texto):
    if not texto:
        return ""
    texto = emoji.replace_emoji(texto, replace="")
    texto = texto.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    texto = texto.replace('"', "&quot;").replace("'", "&apos;")
    return texto.strip()

grupos_norm = {normalize(g): g for g in grupos_desejados}
canais_por_grupo = defaultdict(list)

def obter_epg_corrigido():
    try:
        response = requests.get(EPG_URL, timeout=15)
        epg_str = response.content.decode("utf-8", errors="ignore")
        inicio = epg_str.find("<tv")
        fim = epg_str.rfind("</tv>") + len("</tv>")
        epg_str_corrigido = epg_str[inicio:fim]
        return ET.fromstring(epg_str_corrigido)
    except Exception as e:
        print(f"[ERRO] EPG: {e}")
        return None

epg_tree = obter_epg_corrigido()
if epg_tree is None:
    exit(1)

try:
    response = requests.get(M3U_URL, timeout=15)
    response.encoding = 'utf-8'
    lines = response.text.splitlines()
except Exception as e:
    print(f"[ERRO] Lista M3U: {e}")
    exit(1)

def extrair_grade(epg_channel):
    grade = []
    try:
        for prog in epg_tree.findall(f".//programme[@channel='{epg_channel}']"):
            titulo = limpar_texto(prog.findtext("title", default=""))
            descricao = limpar_texto(prog.findtext("desc", default=""))
            categorias = [limpar_texto(c.text) for c in prog.findall("category") if c.text]

            genero_str = f"[B][COLOR yellow]Gênero:[/COLOR][/B] {', '.join(categorias)}" if categorias else ""
            sinopse_str = f"[B][COLOR yellow]Sinopse:[/COLOR][/B]\n{descricao}" if descricao else ""

            bloco = f"{titulo}"
            if genero_str:
                bloco += f"\n{genero_str}"
            if sinopse_str:
                bloco += f"\n{sinopse_str}"

            grade.append(bloco)
    except SyntaxError:
        return ""
    return "\n\n".join(grade)

i = 0
while i < len(lines):
    if lines[i].startswith("#EXTINF"):
        group_match = re.search(r'group-title="([^"]+)"', lines[i])
        grupo_raw = group_match.group(1) if group_match else None
        grupo = grupos_norm.get(normalize(grupo_raw)) if grupo_raw else None
        if grupo:
            nome_match = re.search(r',(.+)', lines[i])
            if not nome_match:
                i += 2
                continue
            nome = limpar_texto(nome_match.group(1).strip())
            logo = re.search(r'tvg-logo="([^"]+)"', lines[i])
            logo_url = logo.group(1) if logo else ""
            link = lines[i + 1].strip()

            epg_id = re.search(r'tvg-id="([^"]+)"', lines[i])
            epg_channel_raw = epg_id.group(1) if epg_id else nome.lower().replace(" ", "_")

            # Ignorar tvg-id inválido
            if epg_channel_raw.startswith("data:image") or any(c in epg_channel_raw for c in ['<', '>', '"', "'", '[', ']']):
                print(f"[IGNORADO] tvg-id inválido para '{nome}': {epg_channel_raw}")
                i += 2
                continue

            epg_channel = epg_channel_raw
            grade_epg = extrair_grade(epg_channel)
            if not grade_epg:
                print(f"[SEM EPG] {nome}")
                grade_epg = "[COLOR red]Sem programação encontrada[/COLOR]"

            item = f"""<item>
<title>{nome}</title>
<link>{link}</link>
<thumbnail>{logo_url}</thumbnail>
<fanart>https://github.com/AnimeSoul8585/BlackPlay-Tv/raw/refs/heads/main/ICONS%20ADDON/fanart.jpg</fanart>
<info>{grade_epg}</info>
</item>"""

            canais_por_grupo[grupo].append(item)
        i += 2
    else:
        i += 1

output_dir = "BluePlay/FILMES/LINK DIRETO"
os.makedirs(output_dir, exist_ok=True)
output_path = os.path.join(output_dir, "FILMES.xml")

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

print(f"[SUCESSO] Arquivo gerado: {output_path}")
