import re
import os
import requests
import html
import emoji
import xml.etree.ElementTree as ET
from collections import defaultdict

# URLs
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

# Funções auxiliares
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
    return html.escape(texto.strip())

def validar_nome_titulo(titulo):
    if titulo.startswith("/9j/") or "base64" in titulo.lower() or len(titulo) > 200:
        return False
    return True

grupos_norm = {normalize(g): g for g in grupos_desejados}
canais_por_grupo = defaultdict(list)

def obter_epg():
    try:
        r = requests.get(EPG_URL, timeout=15)
        r.encoding = 'utf-8'
        epg_raw = r.text
        inicio = epg_raw.find("<tv")
        fim = epg_raw.rfind("</tv>") + len("</tv>")
        return ET.fromstring(epg_raw[inicio:fim])
    except Exception as e:
        print(f"[ERRO] EPG: {e}")
        return None

epg_tree = obter_epg()
if epg_tree is None:
    exit(1)

try:
    m3u = requests.get(M3U_URL, timeout=15)
    m3u.encoding = 'utf-8'
    lines = m3u.text.splitlines()
except Exception as e:
    print(f"[ERRO] M3U: {e}")
    exit(1)

def extrair_grade(epg_channel):
    grade = []
    try:
        for prog in epg_tree.findall(f".//programme[@channel='{epg_channel}']"):
            titulo = limpar_texto(prog.findtext("title", default=""))
            descricao = limpar_texto(prog.findtext("desc", default=""))
            categorias = [limpar_texto(c.text) for c in prog.findall("category") if c.text]

            genero = f"[B][COLOR yellow]Gênero:[/COLOR][/B] {', '.join(categorias)}" if categorias else ""
            sinopse = f"[B][COLOR yellow]Sinopse:[/COLOR][/B]\\n{descricao}" if descricao else ""

            bloco = f"{titulo}"
            if genero: bloco += f"\\n{genero}"
            if sinopse: bloco += f"\\n{sinopse}"
            grade.append(bloco)
    except:
        return ""
    return "\\n\\n".join(grade)

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

            nome_sujo = nome_match.group(1).strip()
            if not validar_nome_titulo(nome_sujo):
                print(f"[IGNORADO] Nome inválido: {nome_sujo}")
                i += 2
                continue

            nome = limpar_texto(nome_sujo)
            logo = re.search(r'tvg-logo="([^"]+)"', lines[i])
            logo_url = logo.group(1) if logo else ""
            link = lines[i + 1].strip()

            if not nome or not link:
                i += 2
                continue

            epg_id = re.search(r'tvg-id="([^"]+)"', lines[i])
            epg_channel = epg_id.group(1) if epg_id else nome.lower().replace(" ", "_")
            if epg_channel.startswith("data:image") or any(c in epg_channel for c in ['<', '>', '"', "'", '[', ']']):
                print(f"[IGNORADO] tvg-id inválido: {epg_channel}")
                i += 2
                continue

            grade = extrair_grade(epg_channel)
            if not grade:
                print(f"[SEM EPG] {nome}")
                grade = "[COLOR red]Sem programação encontrada[/COLOR]"

            item = f"""<item>
<title>{nome}</title>
<link>{link}</link>
<thumbnail>{logo_url}</thumbnail>
<fanart>https://github.com/AnimeSoul8585/BlackPlay-Tv/raw/refs/heads/main/ICONS%20ADDON/fanart.jpg</fanart>
<info><![CDATA[{grade}]]></info>
</item>"""

            canais_por_grupo[grupo].append(item)
        i += 2
    else:
        i += 1

output_dir = "BluePlay/FILMES/LINK DIRETO"
os.makedirs(output_dir, exist_ok=True)
with open(f"{output_dir}/FILMES.xml", "w", encoding="utf-8") as out:
    out.write('<?xml version="1.0" encoding="UTF-8"?>\n<channels>\n')
    for grupo, canais in canais_por_grupo.items():
        out.write(f"""<channel>
<name>[B][COLOR white]{grupo}[/COLOR][/B]</name>
<thumbnail>https://raw.githubusercontent.com/BluePlay8486/BluePlayHD/main/icon.png</thumbnail>
<fanart>https://github.com/AnimeSoul8585/BlackPlay-Tv/raw/refs/heads/main/ICONS%20ADDON/fanart.jpg</fanart>
<items>\n""")
        out.write("\n".join(sorted(canais)))
        out.write("\n</items>\n</channel>\n")
    out.write("</channels>")

print("[SUCESSO] Arquivo FILMES.xml gerado com sucesso.")
