"""
=============================================================================
REVERSE TEMPLATING POC - Sistema de Identificação e Substituição de Variáveis
=============================================================================

Este script implementa um sistema que:
1. Extrai texto e coordenadas de um PDF usando pdfplumber
2. Usa LLM (Google Gemini) para identificar campos variáveis (Nome, Valor, Data)
3. Cruza os dados da LLM com as coordenadas extraídas
4. Gera um novo PDF com os valores substituídos usando ReportLab

Autor: POC para PitangaTech
Data: Dezembro 2024
"""

import json
import hashlib
import re
from io import BytesIO
from typing import Dict, List, Tuple, Optional

import pdfplumber
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter, A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from PyPDF2 import PdfReader, PdfWriter

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser

import os
from dotenv import load_dotenv

# =============================================================================
# CONFIGURACAO - CARREGA VARIAVEIS DE AMBIENTE
# =============================================================================

load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

if not GOOGLE_API_KEY:
    print("ERRO: GOOGLE_API_KEY nao configurada.")
    print("Crie um arquivo .env com: GOOGLE_API_KEY=sua_chave_aqui")
    print("Obtenha sua chave em: https://aistudio.google.com/app/apikey")
    exit(1)

# =============================================================================
# DADOS MOCKADOS - Novos valores para substituição
# =============================================================================

NOVOS_DADOS = {
    "NOME_CLIENTE": "Maria Oliveira Santos",
    "VALOR_TOTAL": "R$ 1.250,00",
    "DATA_DOCUMENTO": "15/01/2025"
}

# =============================================================================
# BANCO DE TEMPLATES (Simulado em memória para POC)
# =============================================================================

templates_db: Dict[str, dict] = {}


def calcular_hash_documento(pdf_path: str) -> str:
    """
    Calcula um hash do documento para identificar templates conhecidos.
    Na POC, usa o conteúdo textual para gerar o hash.
    """
    with pdfplumber.open(pdf_path) as pdf:
        texto_completo = ""
        for page in pdf.pages:
            texto_completo += page.extract_text() or ""

    # Remove números e valores variáveis para criar hash do "esqueleto"
    texto_normalizado = re.sub(r'\d+', '', texto_completo)
    texto_normalizado = re.sub(r'R\$\s*[\d.,]+', '', texto_normalizado)

    return hashlib.md5(texto_normalizado.encode()).hexdigest()[:16]


# =============================================================================
# ETAPA 1: EXTRAÇÃO - Ler PDF e extrair palavras com coordenadas
# =============================================================================

def extrair_texto_com_coordenadas(pdf_path: str) -> Tuple[str, List[dict]]:
    """
    Extrai todas as palavras do PDF junto com suas bounding boxes.

    Retorna:
        - texto_completo: String com todo o texto da página
        - palavras: Lista de dicts com {text, x0, top, x1, bottom}
    """
    print("\n📖 ETAPA 1: Extraindo texto e coordenadas do PDF...")

    palavras = []
    texto_completo = ""

    with pdfplumber.open(pdf_path) as pdf:
        # Para POC, processamos apenas a primeira página
        page = pdf.pages[0]

        # Extrai texto completo para enviar à LLM
        texto_completo = page.extract_text() or ""

        # Extrai palavras com suas coordenadas (bounding boxes)
        words = page.extract_words(
            keep_blank_chars=False,
            x_tolerance=3,
            y_tolerance=3
        )

        for word in words:
            palavras.append({
                "text": word["text"],
                "x0": word["x0"],      # Coordenada X inicial
                "top": word["top"],    # Coordenada Y inicial (do topo)
                "x1": word["x1"],      # Coordenada X final
                "bottom": word["bottom"],  # Coordenada Y final
                "width": word["x1"] - word["x0"],
                "height": word["bottom"] - word["top"]
            })

        # Guarda dimensões da página para uso posterior
        page_width = page.width
        page_height = page.height

    print(f"   ✓ Texto extraído: {len(texto_completo)} caracteres")
    print(f"   ✓ Palavras encontradas: {len(palavras)}")

    return texto_completo, palavras, (page_width, page_height)


# =============================================================================
# ETAPA 2: ANÁLISE SEMÂNTICA - Usar LLM para identificar variáveis
# =============================================================================

def analisar_com_llm(texto: str) -> Dict[str, str]:
    """
    Envia o texto para o Google Gemini identificar campos variáveis.

    Retorna:
        Dict mapeando texto_original -> tipo_variavel
        Ex: {"João Silva": "NOME_CLIENTE", "R$ 500,00": "VALOR_TOTAL"}
    """
    print("\n🤖 ETAPA 2: Analisando texto com LLM (Gemini)...")

    # Configura o modelo Gemini 2.5 Flash
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash-preview-05-20",
        temperature=0,
        google_api_key=GOOGLE_API_KEY
    )

    # Define o prompt
    prompt = ChatPromptTemplate.from_messages([
        ("system", """Você é um especialista em análise de documentos.
Analise o texto de um documento e identifique APENAS os seguintes tipos de dados variáveis:

1. NOME_CLIENTE: Nome de pessoa ou empresa (cliente, destinatário, etc.)
2. VALOR_TOTAL: Valores monetários no formato brasileiro (R$ X.XXX,XX)
3. DATA_DOCUMENTO: Datas no formato brasileiro (DD/MM/AAAA ou similar)

IMPORTANTE:
- Retorne APENAS um JSON válido, sem markdown ou explicações
- O JSON deve mapear o texto exato encontrado para o tipo de variável
- Identifique no máximo 1 item de cada tipo (o mais relevante)
- Se não encontrar um tipo, não inclua no JSON

Formato de saída esperado:
{{"texto_original_1": "NOME_CLIENTE", "texto_original_2": "VALOR_TOTAL", "texto_original_3": "DATA_DOCUMENTO"}}
"""),
        ("human", "Analise este documento e identifique as variáveis:\n\n{texto}")
    ])

    # Parser para extrair JSON da resposta
    parser = JsonOutputParser()

    # Cria a chain
    chain = prompt | llm | parser

    try:
        resultado = chain.invoke({"texto": texto})
        print(f"   ✓ LLM identificou {len(resultado)} variáveis:")
        for texto_orig, tipo in resultado.items():
            print(f"      - {tipo}: '{texto_orig}'")
        return resultado
    except Exception as e:
        print(f"   ✗ Erro na análise LLM: {e}")
        # Retorna dict vazio em caso de erro
        return {}


# =============================================================================
# ETAPA 3: MAPPER - Cruzar variáveis da LLM com coordenadas
# =============================================================================

def mapear_variaveis_para_coordenadas(
    variaveis_llm: Dict[str, str],
    palavras: List[dict]
) -> List[dict]:
    """
    Cruza os textos identificados pela LLM com as coordenadas do pdfplumber.

    Para textos compostos (ex: "João Silva"), agrupa palavras consecutivas.

    Retorna:
        Lista de dicts com {tipo, texto_original, x0, top, x1, bottom}
    """
    print("\n📍 ETAPA 3: Mapeando variáveis para coordenadas...")

    mapeamentos = []

    for texto_original, tipo_variavel in variaveis_llm.items():
        # Divide o texto em palavras para busca
        palavras_busca = texto_original.split()

        # Busca a sequência de palavras no documento
        for i, palavra in enumerate(palavras):
            # Verifica se encontramos o início da sequência
            if palavra["text"] == palavras_busca[0]:
                # Tenta casar todas as palavras da sequência
                match = True
                coords = {
                    "x0": palavra["x0"],
                    "top": palavra["top"],
                    "x1": palavra["x1"],
                    "bottom": palavra["bottom"]
                }

                for j, palavra_busca in enumerate(palavras_busca[1:], 1):
                    if i + j < len(palavras) and palavras[i + j]["text"] == palavra_busca:
                        # Expande as coordenadas para incluir esta palavra
                        coords["x1"] = palavras[i + j]["x1"]
                        coords["bottom"] = max(coords["bottom"], palavras[i + j]["bottom"])
                    else:
                        match = False
                        break

                if match and len(palavras_busca) == 1:
                    match = True

                if match or len(palavras_busca) == 1:
                    mapeamentos.append({
                        "tipo": tipo_variavel,
                        "texto_original": texto_original,
                        **coords
                    })
                    print(f"   ✓ {tipo_variavel}: '{texto_original}' em ({coords['x0']:.1f}, {coords['top']:.1f})")
                    break

    return mapeamentos


# =============================================================================
# ETAPA 4: GERAÇÃO - Criar novo PDF com overlay
# =============================================================================

def gerar_pdf_com_substituicoes(
    pdf_original: str,
    pdf_saida: str,
    mapeamentos: List[dict],
    novos_valores: Dict[str, str],
    page_size: Tuple[float, float]
) -> None:
    """
    Gera um novo PDF sobrepondo os valores originais com novos valores.

    Processo:
    1. Cria um canvas transparente com ReportLab
    2. Para cada variável: desenha retângulo branco + novo texto
    3. Mescla o overlay com o PDF original usando PyPDF2
    """
    print("\n⚙️ ETAPA 4: Gerando novo PDF com substituições...")

    page_width, page_height = page_size

    # Cria um buffer para o overlay
    overlay_buffer = BytesIO()

    # Cria o canvas do ReportLab
    c = canvas.Canvas(overlay_buffer, pagesize=(page_width, page_height))

    # Configura fonte (usa Helvetica padrão para POC)
    c.setFont("Helvetica", 10)

    for mapeamento in mapeamentos:
        tipo = mapeamento["tipo"]

        if tipo not in novos_valores:
            print(f"   ⚠ Sem novo valor para {tipo}, pulando...")
            continue

        novo_valor = novos_valores[tipo]

        # Coordenadas do pdfplumber (origem no topo-esquerda)
        x0 = mapeamento["x0"]
        top = mapeamento["top"]
        x1 = mapeamento["x1"]
        bottom = mapeamento["bottom"]

        # Converte para coordenadas do ReportLab (origem no bottom-esquerda)
        # ReportLab usa Y invertido em relação ao pdfplumber
        y_reportlab = page_height - bottom
        altura = bottom - top
        largura = x1 - x0

        # Adiciona margem ao retângulo branco para cobrir bem
        margem = 2

        # 1. Desenha retângulo branco para "apagar" o texto original
        c.setFillColorRGB(1, 1, 1)  # Branco
        c.rect(
            x0 - margem,
            y_reportlab - margem,
            largura + (margem * 2) + 20,  # Extra para novos valores maiores
            altura + (margem * 2),
            fill=True,
            stroke=False
        )

        # 2. Escreve o novo valor
        c.setFillColorRGB(0, 0, 0)  # Preto

        # Ajusta tamanho da fonte baseado na altura da caixa
        font_size = min(altura * 0.8, 12)
        c.setFont("Helvetica", font_size)

        # Posiciona o texto (ajuste fino do Y para centralizar)
        y_texto = y_reportlab + (altura * 0.2)
        c.drawString(x0, y_texto, novo_valor)

        print(f"   ✓ {tipo}: '{mapeamento['texto_original']}' → '{novo_valor}'")

    c.save()

    # Mescla overlay com PDF original
    overlay_buffer.seek(0)
    overlay_pdf = PdfReader(overlay_buffer)
    original_pdf = PdfReader(pdf_original)

    writer = PdfWriter()

    # Mescla a primeira página
    page = original_pdf.pages[0]
    page.merge_page(overlay_pdf.pages[0])
    writer.add_page(page)

    # Adiciona as demais páginas sem alteração
    for i in range(1, len(original_pdf.pages)):
        writer.add_page(original_pdf.pages[i])

    # Salva o PDF final
    with open(pdf_saida, "wb") as f:
        writer.write(f)

    print(f"\n   ✓ PDF gerado com sucesso: {pdf_saida}")


# =============================================================================
# ETAPA 5: PERSISTÊNCIA - Salvar/Carregar templates
# =============================================================================

def salvar_template(doc_hash: str, mapeamentos: List[dict]) -> None:
    """Salva o template no banco (simulado em memória para POC)."""
    templates_db[doc_hash] = {
        "hash": doc_hash,
        "mapeamentos": mapeamentos
    }
    print(f"\n💾 Template salvo com hash: {doc_hash}")


def carregar_template(doc_hash: str) -> Optional[List[dict]]:
    """Carrega template do banco se existir."""
    if doc_hash in templates_db:
        print(f"\n💾 Template encontrado para hash: {doc_hash}")
        return templates_db[doc_hash]["mapeamentos"]
    return None


# =============================================================================
# FUNÇÃO PRINCIPAL - Orquestra todo o fluxo
# =============================================================================

def processar_documento(
    pdf_entrada: str,
    pdf_saida: str,
    novos_valores: Dict[str, str],
    forcar_nova_analise: bool = False
) -> None:
    """
    Função principal que orquestra todo o fluxo de reverse templating.

    Args:
        pdf_entrada: Caminho do PDF original
        pdf_saida: Caminho do PDF de saída
        novos_valores: Dict com novos valores para cada tipo de variável
        forcar_nova_analise: Se True, ignora cache e força nova análise LLM
    """
    print("=" * 60)
    print("🚀 REVERSE TEMPLATING POC")
    print("=" * 60)

    # Calcula hash do documento
    doc_hash = calcular_hash_documento(pdf_entrada)
    print(f"\n🔑 Hash do documento: {doc_hash}")

    # Verifica se já conhecemos este template
    mapeamentos = None
    if not forcar_nova_analise:
        mapeamentos = carregar_template(doc_hash)

    # ETAPA 1: Extração (sempre necessária para obter dimensões)
    texto, palavras, page_size = extrair_texto_com_coordenadas(pdf_entrada)

    if mapeamentos is None:
        # FLUXO DE DESCOBERTA (Template Novo)
        print("\n📋 Template não encontrado - Iniciando fluxo de descoberta...")

        # ETAPA 2: Análise com LLM
        variaveis_llm = analisar_com_llm(texto)

        if not variaveis_llm:
            print("\n❌ Não foi possível identificar variáveis no documento.")
            return

        # ETAPA 3: Mapper
        mapeamentos = mapear_variaveis_para_coordenadas(variaveis_llm, palavras)

        # Salva template para uso futuro
        salvar_template(doc_hash, mapeamentos)
    else:
        # FLUXO RÁPIDO (Template Conhecido)
        print("\n⚡ Template encontrado - Usando mapeamentos existentes...")

    # ETAPA 4: Geração do novo PDF
    gerar_pdf_com_substituicoes(
        pdf_entrada,
        pdf_saida,
        mapeamentos,
        novos_valores,
        page_size
    )

    print("\n" + "=" * 60)
    print("✅ PROCESSAMENTO CONCLUÍDO!")
    print("=" * 60)


# =============================================================================
# EXECUÇÃO DO SCRIPT
# =============================================================================

if __name__ == "__main__":
    import sys

    # Configuração padrão
    PDF_ENTRADA = "input.pdf"
    PDF_SAIDA = "output.pdf"

    # Permite passar arquivos via linha de comando
    if len(sys.argv) >= 2:
        PDF_ENTRADA = sys.argv[1]
    if len(sys.argv) >= 3:
        PDF_SAIDA = sys.argv[2]

    print(f"\n📁 Arquivo de entrada: {PDF_ENTRADA}")
    print(f"📁 Arquivo de saída: {PDF_SAIDA}")

    # Executa o processamento
    processar_documento(
        pdf_entrada=PDF_ENTRADA,
        pdf_saida=PDF_SAIDA,
        novos_valores=NOVOS_DADOS,
        forcar_nova_analise=False
    )
