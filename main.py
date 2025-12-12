"""
=============================================================================
REVERSE TEMPLATING POC - Sistema de Identificacao e Substituicao de Variaveis
=============================================================================

Este script implementa um sistema que:
1. Extrai texto e coordenadas de um PDF usando pdfplumber
2. Usa LLM (Google Gemini) para identificar TODOS os campos variaveis
3. Cruza os dados da LLM com as coordenadas extraidas
4. Gera um novo PDF com os valores substituidos usando ReportLab

Suporta qualquer tipo de documento (faturas, contratos, recibos, etc.)

Autor: POC para PitangaTech
Data: Dezembro 2024
"""

import json
import hashlib
import re
import os
from io import BytesIO
from typing import Dict, List, Tuple, Optional

import pdfplumber
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter, A4
from PyPDF2 import PdfReader, PdfWriter

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser

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
# BANCO DE TEMPLATES (Simulado em memoria para POC)
# =============================================================================

templates_db: Dict[str, dict] = {}


def calcular_hash_documento(pdf_path: str) -> str:
    """
    Calcula um hash do documento para identificar templates conhecidos.
    Na POC, usa o conteudo textual para gerar o hash.
    """
    with pdfplumber.open(pdf_path) as pdf:
        texto_completo = ""
        for page in pdf.pages:
            texto_completo += page.extract_text() or ""

    # Remove numeros e valores variaveis para criar hash do "esqueleto"
    texto_normalizado = re.sub(r'\d+', '', texto_completo)
    texto_normalizado = re.sub(r'R\$\s*[\d.,]+', '', texto_normalizado)

    return hashlib.md5(texto_normalizado.encode()).hexdigest()[:16]


# =============================================================================
# ETAPA 1: EXTRACAO - Ler PDF e extrair palavras com coordenadas
# =============================================================================

def extrair_texto_com_coordenadas(pdf_path: str) -> Tuple[str, List[dict], Tuple[float, float]]:
    """
    Extrai todas as palavras do PDF junto com suas bounding boxes.

    Retorna:
        - texto_completo: String com todo o texto da pagina
        - palavras: Lista de dicts com {text, x0, top, x1, bottom}
        - page_size: Tupla com (largura, altura) da pagina
    """
    print("\n[ETAPA 1] Extraindo texto e coordenadas do PDF...")

    palavras = []
    texto_completo = ""

    with pdfplumber.open(pdf_path) as pdf:
        page = pdf.pages[0]
        texto_completo = page.extract_text() or ""

        words = page.extract_words(
            keep_blank_chars=False,
            x_tolerance=3,
            y_tolerance=3
        )

        for word in words:
            palavras.append({
                "text": word["text"],
                "x0": word["x0"],
                "top": word["top"],
                "x1": word["x1"],
                "bottom": word["bottom"],
                "width": word["x1"] - word["x0"],
                "height": word["bottom"] - word["top"]
            })

        page_width = page.width
        page_height = page.height

    print(f"   - Texto extraido: {len(texto_completo)} caracteres")
    print(f"   - Palavras encontradas: {len(palavras)}")

    return texto_completo, palavras, (page_width, page_height)


# =============================================================================
# ETAPA 2: ANALISE SEMANTICA - Usar LLM para identificar variaveis
# =============================================================================

def analisar_com_llm(texto: str) -> List[dict]:
    """
    Envia o texto para o Google Gemini identificar TODOS os campos variaveis.

    Retorna:
        Lista de dicts com {valor_original, tipo, descricao}
    """
    print("\n[ETAPA 2] Analisando texto com LLM (Gemini)...")

    llm = ChatGoogleGenerativeAI(
        model="gemini-1.5-flash",
        temperature=0,
        google_api_key=GOOGLE_API_KEY
    )

    prompt = ChatPromptTemplate.from_messages([
        ("system", """Voce e um especialista em analise de documentos.
Sua tarefa e identificar TODOS os campos variaveis em um documento.

Campos variaveis sao dados que mudam de um documento para outro, como:
- Nomes de pessoas ou empresas
- Datas (qualquer formato)
- Valores monetarios
- Numeros de documentos (CPF, CNPJ, RG, etc.)
- Enderecos
- Telefones e emails
- Numeros de pedido, fatura, contrato
- Quantidades
- Percentuais
- Qualquer outro dado especifico que nao seja texto fixo do template

IMPORTANTE:
- Retorne APENAS um JSON valido, sem markdown ou explicacoes
- O JSON deve ser uma lista de objetos
- Cada objeto deve ter: "valor_original" (texto exato), "tipo" (categoria), "descricao" (label amigavel)
- Identifique o maximo de campos variaveis possiveis
- O "tipo" deve ser um identificador unico em MAIUSCULAS_COM_UNDERSCORE
- A "descricao" deve ser um texto legivel para exibir ao usuario

Exemplo de saida:
[
    {{"valor_original": "Joao Silva", "tipo": "NOME_CLIENTE", "descricao": "Nome do Cliente"}},
    {{"valor_original": "123.456.789-00", "tipo": "CPF_CLIENTE", "descricao": "CPF do Cliente"}},
    {{"valor_original": "10/12/2024", "tipo": "DATA_EMISSAO", "descricao": "Data de Emissao"}},
    {{"valor_original": "R$ 1.500,00", "tipo": "VALOR_TOTAL", "descricao": "Valor Total"}},
    {{"valor_original": "NF-001234", "tipo": "NUMERO_NOTA", "descricao": "Numero da Nota"}}
]
"""),
        ("human", "Analise este documento e identifique TODOS os campos variaveis:\n\n{texto}")
    ])

    parser = JsonOutputParser()
    chain = prompt | llm | parser

    try:
        resultado = chain.invoke({"texto": texto})
        if isinstance(resultado, dict):
            resultado = [resultado]

        print(f"   - LLM identificou {len(resultado)} campos variaveis:")
        for var in resultado:
            print(f"      * {var.get('tipo', 'N/A')}: '{var.get('valor_original', 'N/A')}'")

        return resultado
    except Exception as e:
        print(f"   - ERRO na analise LLM: {e}")
        return []


# =============================================================================
# ETAPA 3: MAPPER - Cruzar variaveis da LLM com coordenadas
# =============================================================================

def mapear_variaveis_para_coordenadas(
    variaveis_llm: List[dict],
    palavras: List[dict]
) -> List[dict]:
    """
    Cruza os textos identificados pela LLM com as coordenadas do pdfplumber.

    Para textos compostos (ex: "Joao Silva"), agrupa palavras consecutivas.

    Retorna:
        Lista de dicts com {tipo, descricao, texto_original, x0, top, x1, bottom}
    """
    print("\n[ETAPA 3] Mapeando variaveis para coordenadas...")

    mapeamentos = []

    for variavel in variaveis_llm:
        texto_original = variavel.get("valor_original", "")
        tipo = variavel.get("tipo", "CAMPO_DESCONHECIDO")
        descricao = variavel.get("descricao", tipo)

        palavras_busca = texto_original.split()
        if not palavras_busca:
            continue

        encontrado = False
        for i, palavra in enumerate(palavras):
            if palavra["text"] == palavras_busca[0]:
                match = True
                coords = {
                    "x0": palavra["x0"],
                    "top": palavra["top"],
                    "x1": palavra["x1"],
                    "bottom": palavra["bottom"]
                }

                for j, palavra_busca in enumerate(palavras_busca[1:], 1):
                    if i + j < len(palavras) and palavras[i + j]["text"] == palavra_busca:
                        coords["x1"] = palavras[i + j]["x1"]
                        coords["bottom"] = max(coords["bottom"], palavras[i + j]["bottom"])
                    else:
                        match = False
                        break

                if match or len(palavras_busca) == 1:
                    mapeamentos.append({
                        "tipo": tipo,
                        "descricao": descricao,
                        "texto_original": texto_original,
                        **coords
                    })
                    print(f"   - {tipo}: '{texto_original}' em ({coords['x0']:.1f}, {coords['top']:.1f})")
                    encontrado = True
                    break

        if not encontrado:
            print(f"   - AVISO: Nao encontrou coordenadas para '{texto_original}'")

    return mapeamentos


# =============================================================================
# ETAPA 4: GERACAO - Criar novo PDF com overlay
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
    2. Para cada variavel: desenha retangulo branco + novo texto
    3. Mescla o overlay com o PDF original usando PyPDF2
    """
    print("\n[ETAPA 4] Gerando novo PDF com substituicoes...")

    page_width, page_height = page_size

    overlay_buffer = BytesIO()
    c = canvas.Canvas(overlay_buffer, pagesize=(page_width, page_height))
    c.setFont("Helvetica", 10)

    substituicoes_feitas = 0

    for mapeamento in mapeamentos:
        tipo = mapeamento["tipo"]

        if tipo not in novos_valores:
            continue

        novo_valor = novos_valores[tipo]

        x0 = mapeamento["x0"]
        top = mapeamento["top"]
        x1 = mapeamento["x1"]
        bottom = mapeamento["bottom"]

        y_reportlab = page_height - bottom
        altura = bottom - top
        largura = x1 - x0
        margem = 2

        largura_novo_texto = len(novo_valor) * 6

        c.setFillColorRGB(1, 1, 1)
        c.rect(
            x0 - margem,
            y_reportlab - margem,
            max(largura, largura_novo_texto) + (margem * 2) + 10,
            altura + (margem * 2),
            fill=True,
            stroke=False
        )

        c.setFillColorRGB(0, 0, 0)
        font_size = min(altura * 0.8, 12)
        c.setFont("Helvetica", font_size)
        y_texto = y_reportlab + (altura * 0.2)
        c.drawString(x0, y_texto, novo_valor)

        print(f"   - {tipo}: '{mapeamento['texto_original']}' -> '{novo_valor}'")
        substituicoes_feitas += 1

    c.save()

    overlay_buffer.seek(0)
    overlay_pdf = PdfReader(overlay_buffer)
    original_pdf = PdfReader(pdf_original)

    writer = PdfWriter()

    page = original_pdf.pages[0]
    page.merge_page(overlay_pdf.pages[0])
    writer.add_page(page)

    for i in range(1, len(original_pdf.pages)):
        writer.add_page(original_pdf.pages[i])

    with open(pdf_saida, "wb") as f:
        writer.write(f)

    print(f"\n   - {substituicoes_feitas} substituicoes realizadas")
    print(f"   - PDF gerado: {pdf_saida}")


# =============================================================================
# ETAPA 5: PERSISTENCIA - Salvar/Carregar templates
# =============================================================================

def salvar_template(doc_hash: str, mapeamentos: List[dict]) -> None:
    """Salva o template no banco (simulado em memoria para POC)."""
    templates_db[doc_hash] = {
        "hash": doc_hash,
        "mapeamentos": mapeamentos
    }
    print(f"\n[CACHE] Template salvo com hash: {doc_hash}")


def carregar_template(doc_hash: str) -> Optional[List[dict]]:
    """Carrega template do banco se existir."""
    if doc_hash in templates_db:
        print(f"\n[CACHE] Template encontrado para hash: {doc_hash}")
        return templates_db[doc_hash]["mapeamentos"]
    return None


# =============================================================================
# FUNCAO PRINCIPAL - Orquestra todo o fluxo
# =============================================================================

def processar_documento(
    pdf_entrada: str,
    pdf_saida: str,
    novos_valores: Dict[str, str] = None,
    forcar_nova_analise: bool = False
) -> List[dict]:
    """
    Funcao principal que orquestra todo o fluxo de reverse templating.

    Args:
        pdf_entrada: Caminho do PDF original
        pdf_saida: Caminho do PDF de saida
        novos_valores: Dict com novos valores para cada tipo de variavel
        forcar_nova_analise: Se True, ignora cache e forca nova analise LLM

    Returns:
        Lista de mapeamentos encontrados (para uso interativo)
    """
    print("=" * 60)
    print("REVERSE TEMPLATING POC")
    print("=" * 60)

    doc_hash = calcular_hash_documento(pdf_entrada)
    print(f"\n[INFO] Hash do documento: {doc_hash}")

    mapeamentos = None
    if not forcar_nova_analise:
        mapeamentos = carregar_template(doc_hash)

    texto, palavras, page_size = extrair_texto_com_coordenadas(pdf_entrada)

    if mapeamentos is None:
        print("\n[INFO] Template nao encontrado - Iniciando analise com IA...")

        variaveis_llm = analisar_com_llm(texto)

        if not variaveis_llm:
            print("\n[ERRO] Nao foi possivel identificar variaveis no documento.")
            return []

        mapeamentos = mapear_variaveis_para_coordenadas(variaveis_llm, palavras)
        salvar_template(doc_hash, mapeamentos)
    else:
        print("\n[INFO] Usando template em cache...")

    # Se novos_valores foi fornecido, gera o PDF
    if novos_valores:
        gerar_pdf_com_substituicoes(
            pdf_entrada,
            pdf_saida,
            mapeamentos,
            novos_valores,
            page_size
        )

        print("\n" + "=" * 60)
        print("PROCESSAMENTO CONCLUIDO!")
        print("=" * 60)
    else:
        print("\n[INFO] Nenhum valor para substituicao fornecido.")
        print("[INFO] Campos identificados:")
        for m in mapeamentos:
            print(f"   - {m['tipo']}: '{m['texto_original']}'")

    return mapeamentos


# =============================================================================
# MODO INTERATIVO
# =============================================================================

def modo_interativo(pdf_entrada: str, pdf_saida: str = "output.pdf"):
    """
    Executa em modo interativo, perguntando ao usuario os novos valores.
    """
    print("\n" + "=" * 60)
    print("MODO INTERATIVO")
    print("=" * 60)

    # Primeiro, analisa o documento
    mapeamentos = processar_documento(pdf_entrada, pdf_saida, novos_valores=None)

    if not mapeamentos:
        print("\nNenhum campo variavel encontrado.")
        return

    print("\n" + "-" * 60)
    print("Digite os novos valores para cada campo (ou ENTER para manter):")
    print("-" * 60)

    novos_valores = {}
    for m in mapeamentos:
        tipo = m["tipo"]
        descricao = m.get("descricao", tipo)
        valor_atual = m["texto_original"]

        novo = input(f"\n{descricao} [atual: {valor_atual}]: ").strip()
        if novo:
            novos_valores[tipo] = novo

    if novos_valores:
        # Recalcula com os novos valores
        doc_hash = calcular_hash_documento(pdf_entrada)
        texto, palavras, page_size = extrair_texto_com_coordenadas(pdf_entrada)

        gerar_pdf_com_substituicoes(
            pdf_entrada,
            pdf_saida,
            mapeamentos,
            novos_valores,
            page_size
        )

        print("\n" + "=" * 60)
        print(f"PDF gerado com sucesso: {pdf_saida}")
        print("=" * 60)
    else:
        print("\nNenhum valor alterado. PDF nao gerado.")


# =============================================================================
# EXECUCAO DO SCRIPT
# =============================================================================

if __name__ == "__main__":
    import sys

    PDF_ENTRADA = "input.pdf"
    PDF_SAIDA = "output.pdf"

    if len(sys.argv) >= 2:
        PDF_ENTRADA = sys.argv[1]
    if len(sys.argv) >= 3:
        PDF_SAIDA = sys.argv[2]

    print(f"\nArquivo de entrada: {PDF_ENTRADA}")
    print(f"Arquivo de saida: {PDF_SAIDA}")

    # Verifica se o arquivo existe
    if not os.path.exists(PDF_ENTRADA):
        print(f"\nERRO: Arquivo '{PDF_ENTRADA}' nao encontrado.")
        print("Use: python main.py <arquivo_entrada.pdf> [arquivo_saida.pdf]")
        exit(1)

    # Executa em modo interativo
    modo_interativo(PDF_ENTRADA, PDF_SAIDA)
