import re
import os
import requests
import html
from collections import defaultdict

M3U_URL = "http://cdn.pthdtv.top:80/get.php?username=630922725&password=280890306&type=m3u_plus&output=mpegts"

grupos_desejados = [
    "LANÇAMENTOS 2025", "LANÇAMENTOS 2024", "LANÇAMENTOS 2023", "LANÇAMENTOS 2022",
    "FILMES | LEGENDADOS", "FILMES DRAMA", "FILMES ROMANCE", "FILMES TERROR", "FILMES AÇÃO",
    "FILMES FICÇÃO", "FILMES AVENTURA", "FILMES FANTASIA", "FILMES | 4K", "FILMES SUSPENSE",
    "FILMES NACIONAL", "FILMES GUERRA", "FILMES PRIME VIDEO", "FILMES ANIMAÇÃO", "FILMES COMÉDIA",
    "FILMES DOCUMENTÁRIOS", "FILMES FAROESTE", "FILMES NETFLIX", "FILMES INFANTIL", "FILMES ANIME",
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

def corrigir_titulo(titulo):
    titulo = html.unescape(titulo).strip()
    if len(titulo) < 3 or "filme" in titulo.lower() and len(titulo.split()) < 2:
        return None
    return titulo.title()

try:
    response = requests.get(M3U_URL, timeout=30)
    lines = response.text.splitlines()
except Exception as e:
    print(f"[ERRO] Falha ao baixar a lista M3U: {e}")
    exit(1)

grupos_norm = {normalize(g): g for g in grupos_desejados}
canais_por_grupo = defaultdict(list)

i = 0
while i < len(lines):
    if lines[i].startswith("#EXTINF"):
        group_match = re.search(r'group-title="([^"]+)"', lines[i])
        grupo_raw = group_match.group(1) if group_match else "OUTROS"
        grupo = grupos_norm.get(normalize(grupo_raw))
        if grupo:
            nome = re.search(r',(.+)', lines[i]).group(1).strip()
            nome_corrigido = corrigir_titulo(nome)
            if not nome_corrigido:
                i += 2
                continue
            logo = re.search(r'tvg-logo="([^"]+)"', lines[i])
            logo_url = logo.group(1) if logo else ""
            link = lines[i + 1].strip()

            item = f"""<item>
<title>{nome_corrigido}</title>
<link>{link}</link>
<thumbnail>{logo_url}</thumbnail>
<fanart>https://github.com/AnimeSoul8585/BlackPlay-Tv/raw/refs/heads/main/ICONS%20ADDON/fanart.jpg</fanart>
<info></info>
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
    for grupo in grupos_desejados:
        canais = canais_por_grupo.get(grupo, [])
        if not canais:
            continue
        canais.sort()
        out.write(f"""<channel>
<name>[B][COLOR white]{grupo}[/COLOR][/B]</name>
<thumbnail>https://github.com/BluePlay8486/BluePlayHD/raw/refs/heads/main/Artes%20Addon/FILMES.png</thumbnail>
<fanart>https://github.com/AnimeSoul8585/BlackPlay-Tv/raw/refs/heads/main/ICONS%20ADDON/fanart.jpg</fanart>
<items>\n""")
        out.write("\n".join(canais))
        out.write("\n</items>\n</channel>\n")
    out.write("</channels>")

print(f"[SUCESSO] Arquivo XML gerado em: {output_path}")
