# src/utils.py

import requests
import re
import xml.etree.ElementTree as ET
from src.config import M3U_URL, TMDB_API_KEY, FANART_URL, GRUPOS_DESEJADOS


def baixar_m3u() -> str:
    try:
        response = requests.get(M3U_URL, timeout=15)
        response.raise_for_status()
        return response.text
    except requests.RequestException as e:
        raise SystemExit(f"Erro ao baixar M3U: {e}")


def parse_m3u(m3u_content: str) -> dict:
    canais_por_grupo = {}
    pattern = r'#EXTINF:-1.*?group-title="(.*?)".*?tvg-logo="(.*?)".*?,(.*?)\n(.*?)\n'

    for match in re.findall(pattern, m3u_content, re.DOTALL):
        grupo, logo, nome, url = match
        if grupo not in GRUPOS_DESEJADOS:
            continue

        if grupo not in canais_por_grupo:
            canais_por_grupo[grupo] = []

        canais_por_grupo[grupo].append({
            "nome": nome.strip(),
            "url": url.strip(),
            "logo": logo.strip() if logo else FANART_URL
        })

    return canais_por_grupo


def buscar_sinopse_tmdb(nome: str) -> str:
    try:
        url = f"https://api.themoviedb.org/3/search/movie"
        params = {
            "api_key": TMDB_API_KEY,
            "query": nome,
            "language": "pt-BR"
        }
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data.get("results"):
            return data["results"][0].get("overview", "Sinopse não encontrada.")
        return "Sinopse não encontrada."
    except Exception:
        return "Sinopse não encontrada."


def gerar_xml(canais_por_grupo: dict, output_path: str):
    root = ET.Element("lista")

    for grupo, canais in canais_por_grupo.items():
        channel = ET.SubElement(root, "channel")
        ET.SubElement(channel, "title").text = grupo
        ET.SubElement(channel, "fanart").text = FANART_URL

        for canal in canais:
            item = ET.SubElement(channel, "item")
            ET.SubElement(item, "title").text = canal["nome"]
            ET.SubElement(item, "link").text = canal["url"]
            ET.SubElement(item, "thumbnail").text = canal["logo"]
            ET.SubElement(item, "info").text = buscar_sinopse_tmdb(canal["nome"])

    tree = ET.ElementTree(root)
    ET.indent(tree, space="  ", level=0)
    tree.write(output_path, encoding="utf-8", xml_declaration=True)
