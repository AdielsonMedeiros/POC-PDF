"""
=============================================================================
REVERSE TEMPLATING POC - Interface Web com Streamlit
=============================================================================

Execute com: streamlit run app.py
"""

import streamlit as st
import json
import hashlib
import re
import tempfile
import os
from io import BytesIO
from typing import Dict, List, Tuple, Optional

import pdfplumber
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from PyPDF2 import PdfReader, PdfWriter

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser

# =============================================================================
# CONFIGURACAO
# =============================================================================

import os
from dotenv import load_dotenv

load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

if not GOOGLE_API_KEY:
    st.error("GOOGLE_API_KEY nao configurada. Crie um arquivo .env com sua chave.")
    st.stop()

# =============================================================================
# CONFIGURACAO DA PAGINA
# =============================================================================

st.set_page_config(
    page_title="Reverse Templating",
    page_icon="page_facing_up",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# CSS customizado - Layout limpo e profissional
st.markdown("""
<style>
    /* Centraliza e limita largura do conteudo */
    .block-container {
        max-width: 1000px;
        padding-top: 3rem;
        padding-bottom: 3rem;
        margin: 0 auto;
    }

    /* Header principal */
    .main-header {
        font-size: 2.2rem;
        font-weight: 600;
        color: #FFFFFF;
        margin-bottom: 0.5rem;
        text-align: center;
    }

    .sub-header {
        font-size: 1rem;
        color: #B0B0B0;
        margin-bottom: 3rem;
        text-align: center;
    }

    /* Titulos de secao */
    .section-title {
        font-size: 1.2rem;
        font-weight: 600;
        color: #FFFFFF;
        margin-bottom: 1.5rem;
        padding-bottom: 0.8rem;
        border-bottom: 2px solid #3B82F6;
    }

    /* Labels dos campos */
    .field-label {
        font-size: 0.95rem;
        font-weight: 500;
        color: #E0E0E0;
        margin-bottom: 0.3rem;
    }

    .field-current {
        font-size: 0.85rem;
        color: #888888;
        margin-bottom: 0.8rem;
        font-style: italic;
    }

    /* Status badges */
    .status-success {
        background-color: #1B4332;
        color: #95D5B2;
        padding: 0.6rem 1.2rem;
        border-radius: 6px;
        font-size: 0.9rem;
        display: inline-block;
    }

    .status-waiting {
        background-color: #1E3A5F;
        color: #90CAF9;
        padding: 0.6rem 1.2rem;
        border-radius: 6px;
        font-size: 0.9rem;
        display: inline-block;
    }

    .status-error {
        background-color: #4A1515;
        color: #EF9A9A;
        padding: 0.6rem 1.2rem;
        border-radius: 6px;
        font-size: 0.9rem;
        display: inline-block;
    }

    /* Ajustes nos botoes */
    .stButton > button {
        border-radius: 6px;
        font-weight: 500;
        padding: 0.6rem 1.5rem;
    }

    /* Upload area */
    .stFileUploader > div > div {
        border-radius: 8px;
    }

    /* Esconde o menu hamburger e footer */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    /* Divisor */
    .divider {
        border-top: 1px solid #333333;
        margin: 2.5rem 0;
    }

    /* Instrucao */
    .instruction-text {
        color: #B0B0B0;
        font-size: 0.95rem;
        margin-bottom: 1.5rem;
    }
</style>
""", unsafe_allow_html=True)


# =============================================================================
# FUNCOES DO PROCESSAMENTO
# =============================================================================

def extrair_texto_com_coordenadas(pdf_file) -> Tuple[str, List[dict], Tuple[float, float]]:
    """Extrai texto e coordenadas do PDF."""
    palavras = []
    texto_completo = ""

    with pdfplumber.open(pdf_file) as pdf:
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

    return texto_completo, palavras, (page_width, page_height)


def analisar_com_llm(texto: str) -> Dict[str, str]:
    """Usa Gemini para identificar variaveis."""
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash-preview-05-20",
        temperature=0,
        google_api_key=GOOGLE_API_KEY
    )

    prompt = ChatPromptTemplate.from_messages([
        ("system", """Voce e um especialista em analise de documentos.
Analise o texto de um documento e identifique APENAS os seguintes tipos de dados variaveis:

1. NOME_CLIENTE: Nome de pessoa ou empresa (cliente, destinatario, etc.)
2. VALOR_TOTAL: Valores monetarios no formato brasileiro (R$ X.XXX,XX)
3. DATA_DOCUMENTO: Datas no formato brasileiro (DD/MM/AAAA ou similar)

IMPORTANTE:
- Retorne APENAS um JSON valido, sem markdown ou explicacoes
- O JSON deve mapear o texto exato encontrado para o tipo de variavel
- Identifique no maximo 1 item de cada tipo (o mais relevante)
- Se nao encontrar um tipo, nao inclua no JSON

Formato de saida esperado:
{{"texto_original_1": "NOME_CLIENTE", "texto_original_2": "VALOR_TOTAL", "texto_original_3": "DATA_DOCUMENTO"}}
"""),
        ("human", "Analise este documento e identifique as variaveis:\n\n{texto}")
    ])

    parser = JsonOutputParser()
    chain = prompt | llm | parser

    try:
        resultado = chain.invoke({"texto": texto})
        return resultado
    except Exception as e:
        st.error(f"Erro na analise: {e}")
        return {}


def mapear_variaveis_para_coordenadas(
    variaveis_llm: Dict[str, str],
    palavras: List[dict]
) -> List[dict]:
    """Cruza variaveis com coordenadas."""
    mapeamentos = []

    for texto_original, tipo_variavel in variaveis_llm.items():
        palavras_busca = texto_original.split()

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
                        "tipo": tipo_variavel,
                        "texto_original": texto_original,
                        **coords
                    })
                    break

    return mapeamentos


def gerar_pdf_com_substituicoes(
    pdf_file,
    mapeamentos: List[dict],
    novos_valores: Dict[str, str],
    page_size: Tuple[float, float]
) -> bytes:
    """Gera novo PDF com valores substituidos."""
    page_width, page_height = page_size

    overlay_buffer = BytesIO()
    c = canvas.Canvas(overlay_buffer, pagesize=(page_width, page_height))
    c.setFont("Helvetica", 10)

    for mapeamento in mapeamentos:
        tipo = mapeamento["tipo"]

        if tipo not in novos_valores or not novos_valores[tipo]:
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

        c.setFillColorRGB(1, 1, 1)
        c.rect(
            x0 - margem,
            y_reportlab - margem,
            largura + (margem * 2) + 50,
            altura + (margem * 2),
            fill=True,
            stroke=False
        )

        c.setFillColorRGB(0, 0, 0)
        font_size = min(altura * 0.8, 12)
        c.setFont("Helvetica", font_size)
        y_texto = y_reportlab + (altura * 0.2)
        c.drawString(x0, y_texto, novo_valor)

    c.save()

    overlay_buffer.seek(0)
    overlay_pdf = PdfReader(overlay_buffer)

    pdf_file.seek(0)
    original_pdf = PdfReader(pdf_file)

    writer = PdfWriter()

    page = original_pdf.pages[0]
    page.merge_page(overlay_pdf.pages[0])
    writer.add_page(page)

    for i in range(1, len(original_pdf.pages)):
        writer.add_page(original_pdf.pages[i])

    output_buffer = BytesIO()
    writer.write(output_buffer)
    output_buffer.seek(0)

    return output_buffer.getvalue()


# =============================================================================
# INTERFACE PRINCIPAL
# =============================================================================

# Header
st.markdown('<h1 class="main-header">Reverse Templating</h1>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">Sistema de identificacao e substituicao de variaveis em documentos PDF</p>', unsafe_allow_html=True)

# Inicializa session state
if 'variaveis_encontradas' not in st.session_state:
    st.session_state.variaveis_encontradas = None
if 'mapeamentos' not in st.session_state:
    st.session_state.mapeamentos = None
if 'page_size' not in st.session_state:
    st.session_state.page_size = None
if 'pdf_processado' not in st.session_state:
    st.session_state.pdf_processado = False
if 'pdf_gerado' not in st.session_state:
    st.session_state.pdf_gerado = None

# =============================================================================
# ETAPA 1: UPLOAD
# =============================================================================

st.markdown('<div class="section-title">Etapa 1: Carregar Documento</div>', unsafe_allow_html=True)

uploaded_file = st.file_uploader(
    "Selecione o arquivo PDF",
    type=['pdf'],
    help="Formatos aceitos: PDF. Tamanho maximo: 200MB"
)

if uploaded_file:
    st.markdown(f'<div class="status-success">Arquivo carregado: {uploaded_file.name}</div>', unsafe_allow_html=True)

    st.markdown("")
    st.markdown("**Visualizacao do documento:**")

    # Centraliza o preview
    col_left, col_center, col_right = st.columns([1, 2, 1])
    with col_center:
        try:
            import fitz
            pdf_bytes = uploaded_file.getvalue()
            doc = fitz.open(stream=pdf_bytes, filetype="pdf")
            page = doc[0]
            pix = page.get_pixmap(matrix=fitz.Matrix(1.5, 1.5))
            img_bytes = pix.tobytes("png")
            st.image(img_bytes, use_container_width=True)
            doc.close()
        except ImportError:
            st.info("Instale PyMuPDF para visualizar: pip install pymupdf")
        except Exception as e:
            st.warning("Nao foi possivel gerar preview")

st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

# =============================================================================
# ETAPA 2: ANALISE
# =============================================================================

if uploaded_file:
    st.markdown('<div class="section-title">Etapa 2: Analise com Inteligencia Artificial</div>', unsafe_allow_html=True)

    st.markdown('<p class="instruction-text">Clique no botao abaixo para identificar automaticamente os campos variaveis do documento.</p>', unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        analisar = st.button("Analisar Documento", type="primary", use_container_width=True)

        if st.session_state.variaveis_encontradas:
            qtd = len(st.session_state.variaveis_encontradas)
            st.markdown(f'<br><div class="status-success">{qtd} campo(s) identificado(s) com sucesso</div>', unsafe_allow_html=True)
        elif not analisar:
            st.markdown('<br><div class="status-waiting">Aguardando analise do documento</div>', unsafe_allow_html=True)

    if analisar:
        with st.spinner("Extraindo texto do documento..."):
            uploaded_file.seek(0)
            texto, palavras, page_size = extrair_texto_com_coordenadas(uploaded_file)
            st.session_state.page_size = page_size

        with st.spinner("Identificando campos variaveis com IA..."):
            variaveis = analisar_com_llm(texto)

        if variaveis:
            mapeamentos = mapear_variaveis_para_coordenadas(variaveis, palavras)
            st.session_state.variaveis_encontradas = variaveis
            st.session_state.mapeamentos = mapeamentos
            st.session_state.pdf_processado = True
            st.rerun()
        else:
            st.error("Nao foi possivel identificar campos variaveis no documento.")

    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

# =============================================================================
# ETAPA 3: EDICAO
# =============================================================================

if st.session_state.variaveis_encontradas:
    st.markdown('<div class="section-title">Etapa 3: Definir Novos Valores</div>', unsafe_allow_html=True)

    st.markdown('<p class="instruction-text">Preencha os campos abaixo com os novos valores que devem substituir os originais:</p>', unsafe_allow_html=True)

    novos_valores = {}

    # Inverte o dicionario para agrupar por tipo
    tipos_variaveis = {}
    for texto, tipo in st.session_state.variaveis_encontradas.items():
        tipos_variaveis[tipo] = texto

    # Cria colunas para os campos
    cols = st.columns(3)

    campo_idx = 0

    if "NOME_CLIENTE" in tipos_variaveis:
        with cols[campo_idx % 3]:
            st.markdown('<p class="field-label">Nome do Cliente</p>', unsafe_allow_html=True)
            st.markdown(f'<p class="field-current">Valor atual: {tipos_variaveis["NOME_CLIENTE"]}</p>', unsafe_allow_html=True)
            novos_valores["NOME_CLIENTE"] = st.text_input(
                "nome",
                value="",
                placeholder="Digite o novo nome",
                label_visibility="collapsed",
                key="nome_input"
            )
        campo_idx += 1

    if "VALOR_TOTAL" in tipos_variaveis:
        with cols[campo_idx % 3]:
            st.markdown('<p class="field-label">Valor Total</p>', unsafe_allow_html=True)
            st.markdown(f'<p class="field-current">Valor atual: {tipos_variaveis["VALOR_TOTAL"]}</p>', unsafe_allow_html=True)
            novos_valores["VALOR_TOTAL"] = st.text_input(
                "valor",
                value="",
                placeholder="Ex: R$ 1.500,00",
                label_visibility="collapsed",
                key="valor_input"
            )
        campo_idx += 1

    if "DATA_DOCUMENTO" in tipos_variaveis:
        with cols[campo_idx % 3]:
            st.markdown('<p class="field-label">Data do Documento</p>', unsafe_allow_html=True)
            st.markdown(f'<p class="field-current">Valor atual: {tipos_variaveis["DATA_DOCUMENTO"]}</p>', unsafe_allow_html=True)
            novos_valores["DATA_DOCUMENTO"] = st.text_input(
                "data",
                value="",
                placeholder="Ex: 15/01/2025",
                label_visibility="collapsed",
                key="data_input"
            )

    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

    # =============================================================================
    # ETAPA 4: GERACAO
    # =============================================================================

    st.markdown('<div class="section-title">Etapa 4: Gerar Documento</div>', unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        gerar = st.button("Gerar PDF com novos valores", type="primary", use_container_width=True)

        if gerar:
            valores_preenchidos = {k: v for k, v in novos_valores.items() if v}

            if not valores_preenchidos:
                st.warning("Preencha pelo menos um campo com novo valor.")
            else:
                with st.spinner("Gerando documento..."):
                    uploaded_file.seek(0)
                    pdf_bytes = gerar_pdf_com_substituicoes(
                        uploaded_file,
                        st.session_state.mapeamentos,
                        novos_valores,
                        st.session_state.page_size
                    )
                    st.session_state.pdf_gerado = pdf_bytes

        if st.session_state.pdf_gerado:
            st.markdown('<br>', unsafe_allow_html=True)
            st.download_button(
                label="Baixar documento modificado",
                data=st.session_state.pdf_gerado,
                file_name="documento_modificado.pdf",
                mime="application/pdf",
                use_container_width=True
            )

    # Preview do PDF gerado
    if st.session_state.pdf_gerado:
        st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
        st.markdown('<div class="section-title">Resultado Final</div>', unsafe_allow_html=True)

        col_left, col_center, col_right = st.columns([1, 2, 1])
        with col_center:
            try:
                import fitz
                doc = fitz.open(stream=st.session_state.pdf_gerado, filetype="pdf")
                page = doc[0]
                pix = page.get_pixmap(matrix=fitz.Matrix(1.5, 1.5))
                img_bytes = pix.tobytes("png")
                st.image(img_bytes, use_container_width=True)
                doc.close()
            except:
                st.success("Documento gerado com sucesso! Clique em 'Baixar' acima.")

else:
    if uploaded_file:
        st.info("Clique em 'Analisar Documento' para identificar os campos variaveis.")
