import re
import os
import requests
import html
import emoji
import xml.etree.ElementTree as ET
from collections import defaultdict

# URLs e caminho de saída
EPG_URL = "https://raw.githubusercontent.com/BluePlay8486/BluePlayHD/main/EPG/epg.xml"
M3U_URL = "http://cdn.pthdtv.top:80/get.php?username=630922725&password=280890306&type=m3u_plus&output=mpegts"
OUTPUT_PATH = "BluePlay/FILMES/LINK DIRETO/FILMES.xml"
FANART_URL = "https://github.com/AnimeSoul8585/BlackPlay-Tv/raw/refs/heads/main/ICONS%20ADDON/fanart.jpg"
THUMBNAIL_DEFAULT = "https://raw.githubusercontent.com/BluePlay8486/BluePlayHD/main/icon.png"

# Grupos desejados
grupos_desejados = [
    "LANÇAMENTOS 2025",
    "LANÇAMENTOS 2024",
    "LANÇAMENTOS 2023",
    "LANÇAMENTOS 2022",
    "FILMES | LEGENDADOS",
    "FILMES DRAMA",
    "FILMES ROMANCE",
    "FILMES TERROR",
    "FILMES AÇÃO",
    "FILMES FICÇÃO",
    "FILMES AVENTURA",
    "FILMES FANTASIA",
    "FILMES | 4K",
    "FILMES SUSPENSE",
    "FILMES NACIONAL",
    "FILMES GUERRA",
    "FILMES PRIME VIDEO",
    "FILMES ANIMAÇÃO",
    "FILMES COMÉDIA",
    "FILMES DOCUMENTÁRIOS",
    "FILMES FAROESTE",
    "FILMES NETFLIX",
    "FILMES INFANTIL",
    "FILMES ANIME",
    "FILMES DISNEY+",
    "FILMES APPLE TV+",
    "FILMES GLOBOPLAY",
    "FILMES PARAMOUNT+",
    "FILMES HBO MAX",
    "FILMES STAR+",
    "FILMES CRIME",
    "FILMES | COPA DO MUNDO 2022",
    "FILMES RELIGIOSOS",
    "FILMES BRASIL PARALELO",
    "FILMES | DESPERTAR UMA NOVA CONSCIÊNCIA",
    "FILMES | SONS PARA DORMIR",
    "FILMES DC COMICS",
    "FILMES MARVEL",
    "FILMES | 007 COLEÇÃO"
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
    return not (
        titulo.startswith("/9j/") or
        "base64" in titulo.lower() or
        len(titulo) > 200
    )

def obter_epg():
    try:
        r = requests.get(EPG_URL, timeout=15)
        r.encoding = 'utf-8'
        raw = r.text
        return ET.fromstring(raw[raw.find("<tv"):raw.rfind("</tv>")+5])
    except Exception as e:
        print(f"[ERRO] Falha ao carregar EPG: {e}")
        return None

def extrair_grade(epg, canal_id):
    try:
        blocos = []
        for prog in epg.findall(f".//programme[@channel='{canal_id}']"):
            titulo = limpar_texto(prog.findtext("title", default=""))
            desc = limpar_texto(prog.findtext("desc", default=""))
            categorias = [limpar_texto(c.text) for c in prog.findall("category") if c.text]
            bloco = f"{titulo}"
            if categorias:
                bloco += f"\n[B][COLOR yellow]Gênero:[/COLOR][/B] {', '.join(categorias)}"
            if desc:
                bloco += f"\n[B][COLOR yellow]Sinopse:[/COLOR][/B]\n{desc}"
            blocos.append(bloco)
        return "\n\n".join(blocos)
    except:
        return ""

# Início do processamento
epg_tree = obter_epg()
if not epg_tree:
    exit(1)

try:
    m3u = requests.get(M3U_URL, timeout=15)
    m3u.encoding = 'utf-8'
    lines = m3u.text.splitlines()
except Exception as e:
    print(f"[ERRO] Falha ao baixar lista M3U: {e}")
    exit(1)

# Mapeamento e extração
grupos_norm = {normalize(g): g for g in grupos_desejados}
canais_por_grupo = defaultdict(list)
i = 0

while i < len(lines):
    if lines[i].startswith("#EXTINF"):
        grupo_raw = re.search(r'group-title="([^"]+)"', lines[i])
        grupo = grupos_norm.get(normalize(grupo_raw.group(1))) if grupo_raw else None

        if grupo:
            nome_raw = re.search(r',(.+)', lines[i])
            if not nome_raw:
                i += 2
                continue

            nome_sujo = nome_raw.group(1).strip()
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
            canal_id = epg_id.group(1) if epg_id else nome.lower().replace(" ", "_")

            if any(x in canal_id for x in ['<', '>', '"', "'", '[', ']', 'data:image']):
                print(f"[IGNORADO] tvg-id inválido: {canal_id}")
                i += 2
                continue

            grade = extrair_grade(epg_tree, canal_id)
            if not grade:
                grade = "[COLOR red]Sem programação encontrada[/COLOR]"

            item = f"""<item>
<title>{nome}</title>
<link>{link}</link>
<thumbnail>{logo_url}</thumbnail>
<fanart>{FANART_URL}</fanart>
<info><![CDATA[{grade}]]></info>
</item>"""

            canais_por_grupo[grupo].append(item)
        i += 2
    else:
        i += 1

# Geração do XML
os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
    f.write('<?xml version="1.0" encoding="UTF-8"?>\n<channels>\n')
    for grupo, canais in canais_por_grupo.items():
        f.write(f"""<channel>
<name>[B][COLOR white]{grupo}[/COLOR][/B]</name>
<thumbnail>{THUMBNAIL_DEFAULT}</thumbnail>
<fanart>{FANART_URL}</fanart>
<items>\n""")
        f.write("\n".join(sorted(canais)))
        f.write("\n</items>\n</channel>\n")
    f.write("</channels>")

print(f"[OK] XML gerado em: {OUTPUT_PATH}")

# Validação do XML gerado
print("\n[VALIDAÇÃO] Verificando XML...")
try:
    ET.parse(OUTPUT_PATH)
    print("[VALIDADO] XML bem formado e pronto para uso.")
except Exception as e:
    print(f"[ERRO XML] O XML possui erro: {e}")
