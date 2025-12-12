"""
=============================================================================
REVERSE TEMPLATING POC - Interface Web com Streamlit
=============================================================================

Suporta qualquer tipo de documento PDF, identificando automaticamente
todos os campos variaveis encontrados.

Inclui OCR para PDFs escaneados (requer Tesseract instalado).

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

from dotenv import load_dotenv

# Importa o motor de OCR
from ocr_engine import (
    extrair_texto_automatico,
    verificar_tesseract_instalado,
    TESSERACT_DISPONIVEL
)

# Importa o banco de dados
from database import (
    salvar_template,
    carregar_template,
    listar_templates,
    template_existe,
    contar_templates
)

# =============================================================================
# CONFIGURACAO
# =============================================================================

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

    /* Campo variavel */
    .field-card {
        background-color: #1a1a2e;
        border: 1px solid #333;
        border-radius: 8px;
        padding: 1rem;
        margin-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)


# =============================================================================
# FUNCOES DO PROCESSAMENTO
# =============================================================================

def calcular_hash_documento(pdf_file) -> str:
    """
    Calcula um hash do documento para identificar templates conhecidos.
    Usa o conteudo do PDF para gerar um hash unico.
    """
    import hashlib
    import re

    if hasattr(pdf_file, 'seek'):
        pdf_file.seek(0)

    try:
        with pdfplumber.open(pdf_file) as pdf:
            texto_completo = ""
            for page in pdf.pages:
                texto_completo += page.extract_text() or ""

        # Remove numeros e valores variaveis para criar hash do "esqueleto"
        texto_normalizado = re.sub(r'\d+', '', texto_completo)
        texto_normalizado = re.sub(r'R\$\s*[\d.,]+', '', texto_normalizado)

        return hashlib.md5(texto_normalizado.encode()).hexdigest()[:16]
    except:
        # Fallback: usa hash do arquivo
        if hasattr(pdf_file, 'seek'):
            pdf_file.seek(0)
        conteudo = pdf_file.read() if hasattr(pdf_file, 'read') else pdf_file
        if hasattr(pdf_file, 'seek'):
            pdf_file.seek(0)
        return hashlib.md5(conteudo).hexdigest()[:16]


def extrair_texto_com_coordenadas(pdf_file, forcar_ocr: bool = False) -> Tuple[str, List[dict], Tuple[float, float], str]:
    """
    Extrai texto e coordenadas do PDF.
    Detecta automaticamente se deve usar OCR ou extracao nativa.

    Returns:
        - texto_completo: String com todo o texto
        - palavras: Lista de dicts com coordenadas
        - page_size: Tupla (largura, altura)
        - metodo: Metodo usado ("pdfplumber" ou "tesseract")
    """
    texto, palavras, page_size, metodo = extrair_texto_automatico(
        pdf_file,
        forcar_ocr=forcar_ocr,
        idioma_ocr="por+eng"
    )

    return texto, palavras, page_size, metodo


def analisar_com_llm(texto: str) -> List[dict]:
    """
    Usa Gemini para identificar TODOS os campos variaveis do documento.
    Retorna uma lista de dicionarios com informacoes de cada campo.
    """
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash-preview-05-20",
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
        # Garante que o resultado e uma lista
        if isinstance(resultado, dict):
            resultado = [resultado]
        return resultado
    except Exception as e:
        st.error(f"Erro na analise: {e}")
        return []


def mapear_variaveis_para_coordenadas(
    variaveis_llm: List[dict],
    palavras: List[dict]
) -> List[dict]:
    """Cruza variaveis com coordenadas."""
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
                    encontrado = True
                    break

        # Se nao encontrou com match exato, tenta busca parcial
        if not encontrado and len(palavras_busca) == 1:
            for palavra in palavras:
                if palavras_busca[0] in palavra["text"] or palavra["text"] in palavras_busca[0]:
                    mapeamentos.append({
                        "tipo": tipo,
                        "descricao": descricao,
                        "texto_original": texto_original,
                        "x0": palavra["x0"],
                        "top": palavra["top"],
                        "x1": palavra["x1"],
                        "bottom": palavra["bottom"]
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

        # Calcula largura necessaria para o novo texto
        largura_novo_texto = len(novo_valor) * 6  # Estimativa aproximada

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
if 'metodo_extracao' not in st.session_state:
    st.session_state.metodo_extracao = None
if 'doc_hash' not in st.session_state:
    st.session_state.doc_hash = None
if 'template_do_banco' not in st.session_state:
    st.session_state.template_do_banco = False

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

        if st.session_state.mapeamentos:
            qtd = len(st.session_state.mapeamentos)
            metodo = st.session_state.metodo_extracao or "pdfplumber"

            if "banco" in metodo.lower() or st.session_state.template_do_banco:
                metodo_label = "Template salvo (instantaneo)"
            elif "tesseract" in metodo:
                metodo_label = "OCR (Tesseract)"
            else:
                metodo_label = "Texto nativo"

            st.markdown(f'<br><div class="status-success">{qtd} campo(s) identificado(s) via {metodo_label}</div>', unsafe_allow_html=True)
        elif not analisar:
            st.markdown('<br><div class="status-waiting">Aguardando analise do documento</div>', unsafe_allow_html=True)

    if analisar:
        # Primeiro, calcula o hash do documento
        with st.spinner("Verificando documento..."):
            uploaded_file.seek(0)
            doc_hash = calcular_hash_documento(uploaded_file)
            st.session_state.doc_hash = doc_hash

            # Verifica se ja temos esse template no banco
            mapeamentos_banco = carregar_template(doc_hash)

        if mapeamentos_banco:
            # Template encontrado no banco - usa direto!
            st.session_state.mapeamentos = mapeamentos_banco
            st.session_state.template_do_banco = True
            st.session_state.metodo_extracao = "banco de dados (cache)"

            # Ainda precisa extrair page_size
            uploaded_file.seek(0)
            with pdfplumber.open(uploaded_file) as pdf:
                page = pdf.pages[0]
                st.session_state.page_size = (page.width, page.height)

            st.session_state.pdf_processado = True
            st.session_state.pdf_gerado = None
            st.rerun()

        else:
            # Template novo - analisa com IA
            with st.spinner("Extraindo texto do documento..."):
                uploaded_file.seek(0)
                texto, palavras, page_size, metodo = extrair_texto_com_coordenadas(uploaded_file)
                st.session_state.page_size = page_size
                st.session_state.metodo_extracao = metodo

            with st.spinner("Identificando campos variaveis com IA..."):
                variaveis = analisar_com_llm(texto)

            if variaveis:
                mapeamentos = mapear_variaveis_para_coordenadas(variaveis, palavras)
                st.session_state.variaveis_encontradas = variaveis
                st.session_state.mapeamentos = mapeamentos
                st.session_state.template_do_banco = False
                st.session_state.pdf_processado = True
                st.session_state.pdf_gerado = None

                # Salva o template no banco para uso futuro
                with st.spinner("Salvando template..."):
                    salvar_template(doc_hash, mapeamentos)

                st.rerun()
            else:
                st.error("Nao foi possivel identificar campos variaveis no documento.")

    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

# =============================================================================
# ETAPA 3: EDICAO
# =============================================================================

if st.session_state.mapeamentos:
    st.markdown('<div class="section-title">Etapa 3: Definir Novos Valores</div>', unsafe_allow_html=True)

    st.markdown('<p class="instruction-text">Preencha os campos abaixo com os novos valores que devem substituir os originais. Deixe em branco os campos que nao deseja alterar.</p>', unsafe_allow_html=True)

    novos_valores = {}

    # Calcula numero de colunas baseado na quantidade de campos
    num_campos = len(st.session_state.mapeamentos)
    num_colunas = min(3, num_campos)  # Maximo 3 colunas

    # Cria campos dinamicamente
    if num_campos > 0:
        # Organiza em linhas de 3 colunas
        for i in range(0, num_campos, 3):
            cols = st.columns(3)
            for j in range(3):
                idx = i + j
                if idx < num_campos:
                    mapeamento = st.session_state.mapeamentos[idx]
                    tipo = mapeamento["tipo"]
                    descricao = mapeamento.get("descricao", tipo)
                    valor_atual = mapeamento["texto_original"]

                    with cols[j]:
                        st.markdown(f'<p class="field-label">{descricao}</p>', unsafe_allow_html=True)
                        st.markdown(f'<p class="field-current">Valor atual: {valor_atual}</p>', unsafe_allow_html=True)
                        novos_valores[tipo] = st.text_input(
                            descricao,
                            value="",
                            placeholder=f"Novo valor para {descricao.lower()}",
                            label_visibility="collapsed",
                            key=f"input_{tipo}_{idx}"
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
                st.rerun()

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
