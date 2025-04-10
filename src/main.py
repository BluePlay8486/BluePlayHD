# src/main.py

from utils import baixar_m3u, parse_m3u, gerar_xml
from config import OUTPUT_XML_PATH


def main():
    print("Iniciando geração do XML personalizado...")
    
    print("Baixando lista M3U...")
    m3u_content = baixar_m3u()
    print("Download da M3U concluído.")

    print("Processando lista e filtrando grupos desejados...")
    canais_por_grupo = parse_m3u(m3u_content)
    print(f"Total de grupos encontrados: {len(canais_por_grupo)}")

    print("Gerando arquivo XML final...")
    gerar_xml(canais_por_grupo, OUTPUT_XML_PATH)
    print(f"XML gerado com sucesso em: {OUTPUT_XML_PATH}")


if __name__ == "__main__":
    main()
