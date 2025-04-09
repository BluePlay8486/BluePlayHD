import requests
import re
import xml.etree.ElementTree as ET
from datetime import datetime
from xml.dom import minidom

M3U_URL = "https://raw.githubusercontent.com/BluePlay8486/BluePlayHD/main/BluePlay/FILMES/LINK%20DIRETO/FILMES.txt"
EPG_URL = "https://raw.githubusercontent.com/BluePlay8486/BluePlayHD/refs/heads/main/EPG/epg.xml"
FANART_URL = "https://github.com/AnimeSoul8585/BlackPlay-Tv/raw/refs/heads/main/ICONS%20ADDON/fanart.jpg"
THUMBNAIL_DEFAULT = "https://raw.githubusercontent.com/BluePlay8486/BluePlayHD/main/icon.png"
OUTPUT_XML = "BluePlay/FILMES/LINK DIRETO/FILMES.xml"

GRUPOS_ORDEM = [
    "LANÇAMENTOS 2025", "LANÇAMENTOS 2024", "LANÇAMENTOS 2023", "LANÇAMENTOS 2022",
    "FILMES | LEGENDADOS", "FILMES DRAMA", "FILMES ROMANCE", "FILMES TERROR", "FILMES AÇÃO",
    "FILMES FICÇÃO", "FILMES AVENTURA", "FILMES FANTASIA", "FILMES | 4K", "FILMES SUSPENSE",
    "FILMES NACIONAL", "FILMES GUERRA", "FILMES PRIME VIDEO", "FILMES ANIMAÇÃO", "FILMES COMÉDIA",
    "FILMES DOCUMENTÁRIOS", "FILMES FAROESTE", "FILMES NETFLIX", "FILMES INFANTIL", "FILMES ANIME",
    "FILMES DISNEY+", "FILMES APPLE TV+", "FILMES GLOBOPLAY", "FILMES PARAMOUNT+",
    "FILMES HBO MAX", "FILMES STAR+", "FILMES CRIME", "FILMES | COPA DO MUNDO 2022",
    "FILMES RELIGIOSOS", "FILMES BRASIL PARALELO", "FILMES | DESPERTAR UMA NOVA CONSCIÊNCIA",
    "FILMES | SONS PARA DORMIR", "FILMES DC COMICS", "FILMES MARVEL", "FILMES | 007 COLEÇÃO"
]

def baixar_m3u(url):
    print("[INFO] Baixando lista M3U...")
    r = requests.get(url)
    if r.status_code != 200:
        print(f"[ERRO] Falha ao baixar M3U. Código HTTP: {r.status_code}")
        exit(1)
    return r.text

def baixar_epg(url):
    print("[INFO] Baixando grade EPG...")
    r = requests.get(url)
    if r.status_code != 200:
        print(f"[ERRO] Falha ao baixar EPG. Código HTTP: {r.status_code}")
        exit(1)
    return ET.fromstring(r.content)

def extrair_programacao(epg, tvg_id):
    hoje = datetime.now().strftime("%Y%m%d")
    programas = []
    for prog in epg.findall("programme"):
        if prog.attrib.get("channel") == tvg_id and prog.attrib.get("start", "").startswith(hoje):
            inicio = prog.attrib.get("start")[8:12]
            titulo = prog.findtext("title", default="Sem título")
            programas.append(f"{inicio[:2]}:{inicio[2:]} - {titulo}")
    return programas if programas else ["[SEM EPG] Nenhuma programação encontrada para hoje."]

def parsear_m3u(m3u_text):
    canais_por_grupo = {g: [] for g in GRUPOS_ORDEM}
    pattern = re.compile(r'#EXTINF:-1.*?tvg-id="(.*?)".*?tvg-logo="(.*?)".*?group-title="(.*?)".*?,(.*?)\n(.*?)\n')
    matches = pattern.findall(m3u_text)
    for tvg_id, logo, grupo, titulo, link in matches:
        grupo = grupo.strip()
        if grupo in canais_por_grupo:
            canais_por_grupo[grupo].append({
                "tvg_id": tvg_id.strip(),
                "logo": logo.strip() or THUMBNAIL_DEFAULT,
                "titulo": titulo.strip(),
                "link": link.strip()
            })
    return canais_por_grupo

def criar_xml(canais_por_grupo, epg):
    print("[INFO] Gerando XML estruturado...")
    root = ET.Element("canais")
    for grupo in GRUPOS_ORDEM:
        canais = canais_por_grupo.get(grupo, [])
        if not canais:
            continue
        canal_tag = ET.SubElement(root, "channel", label=grupo)
        for canal in canais:
            item = ET.SubElement(canal_tag, "item")
            ET.SubElement(item, "title").text = canal["titulo"]
            ET.SubElement(item, "link").text = canal["link"]
            ET.SubElement(item, "thumbnail").text = canal["logo"] or THUMBNAIL_DEFAULT
            ET.SubElement(item, "fanart").text = FANART_URL
            info = ET.SubElement(item, "info")
            grade = extrair_programacao(epg, canal["tvg_id"])
            info.text = "\n".join(grade)
    return minidom.parseString(ET.tostring(root, encoding="utf-8")).toprettyxml(indent="  ", encoding="utf-8")

def validar_xml(caminho_arquivo):
    try:
        print(f"[VALIDAÇÃO] Verificando integridade do arquivo XML: {caminho_arquivo}")
        ET.parse(caminho_arquivo)
        print("[SUCESSO] XML validado com sucesso!")
        return True
    except ET.ParseError as e:
        print(f"[ERRO] XML inválido: {e}")
        return False
    except Exception as e:
        print(f"[ERRO] Falha na validação do XML: {e}")
        return False

def main():
    m3u = baixar_m3u(M3U_URL)
    epg = baixar_epg(EPG_URL)
    canais = parsear_m3u(m3u)
    xml_bytes = criar_xml(canais, epg)

    with open(OUTPUT_XML, "wb") as f:
        f.write(xml_bytes)
        print(f"[SUCESSO] XML salvo em: {OUTPUT_XML}")

    if not validar_xml(OUTPUT_XML):
        print("[ERRO] Processo interrompido devido a falha na estrutura do XML.")
        exit(1)

if __name__ == "__main__":
    main()
