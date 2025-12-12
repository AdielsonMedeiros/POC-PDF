"""
=============================================================================
OCR ENGINE - Extracao de texto com Tesseract
=============================================================================

Este modulo fornece funcoes para:
1. Detectar se um PDF e escaneado ou tem texto nativo
2. Extrair texto com coordenadas usando Tesseract OCR
3. Converter PDF para imagem para processamento OCR

Requer instalacao do Tesseract:
- Windows: https://github.com/UB-Mannheim/tesseract/wiki
- Linux: sudo apt-get install tesseract-ocr tesseract-ocr-por
- Mac: brew install tesseract
"""

import os
import sys
from io import BytesIO
from typing import List, Tuple, Optional
from PIL import Image

# Tenta importar as dependencias de OCR
try:
    import pytesseract
    TESSERACT_DISPONIVEL = True
except ImportError:
    TESSERACT_DISPONIVEL = False

try:
    import fitz  # PyMuPDF
    PYMUPDF_DISPONIVEL = True
except ImportError:
    PYMUPDF_DISPONIVEL = False

try:
    import pdfplumber
    PDFPLUMBER_DISPONIVEL = True
except ImportError:
    PDFPLUMBER_DISPONIVEL = False


def verificar_tesseract_instalado() -> bool:
    """
    Verifica se o Tesseract esta instalado no sistema.
    """
    if not TESSERACT_DISPONIVEL:
        return False

    try:
        pytesseract.get_tesseract_version()
        return True
    except Exception:
        return False


def configurar_tesseract_windows():
    """
    Tenta configurar o caminho do Tesseract no Windows.
    """
    if sys.platform == 'win32' and TESSERACT_DISPONIVEL:
        # Caminhos comuns de instalacao no Windows
        caminhos_possiveis = [
            r'C:\Program Files\Tesseract-OCR\tesseract.exe',
            r'C:\Program Files (x86)\Tesseract-OCR\tesseract.exe',
            r'C:\Tesseract-OCR\tesseract.exe',
        ]

        for caminho in caminhos_possiveis:
            if os.path.exists(caminho):
                pytesseract.pytesseract.tesseract_cmd = caminho
                return True

    return False


# Configura automaticamente ao importar o modulo
if TESSERACT_DISPONIVEL:
    configurar_tesseract_windows()


def detectar_pdf_escaneado(pdf_file, limiar_caracteres: int = 50) -> bool:
    """
    Detecta se um PDF e escaneado (imagem) ou tem texto nativo.

    Args:
        pdf_file: Arquivo PDF (file-like object ou caminho)
        limiar_caracteres: Numero minimo de caracteres para considerar como texto nativo

    Returns:
        True se o PDF parece ser escaneado, False se tem texto nativo
    """
    if not PDFPLUMBER_DISPONIVEL:
        return True  # Assume escaneado se nao puder verificar

    try:
        with pdfplumber.open(pdf_file) as pdf:
            # Verifica a primeira pagina
            if len(pdf.pages) == 0:
                return True

            page = pdf.pages[0]
            texto = page.extract_text() or ""

            # Se tem menos caracteres que o limiar, provavelmente e escaneado
            # Remove espacos para contar apenas caracteres reais
            texto_limpo = texto.replace(" ", "").replace("\n", "")

            return len(texto_limpo) < limiar_caracteres

    except Exception:
        return True  # Em caso de erro, assume escaneado


def pdf_para_imagens(pdf_file, dpi: int = 300) -> List[Image.Image]:
    """
    Converte paginas de um PDF em imagens PIL.

    Args:
        pdf_file: Arquivo PDF (bytes ou file-like object)
        dpi: Resolucao da imagem (maior = melhor OCR, mais lento)

    Returns:
        Lista de imagens PIL, uma por pagina
    """
    if not PYMUPDF_DISPONIVEL:
        raise ImportError("PyMuPDF (fitz) nao esta instalado. Execute: pip install pymupdf")

    imagens = []

    # Se for file-like object, le os bytes
    if hasattr(pdf_file, 'read'):
        pdf_file.seek(0)
        pdf_bytes = pdf_file.read()
        pdf_file.seek(0)
    else:
        pdf_bytes = pdf_file

    # Abre o PDF com PyMuPDF
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")

    for page_num in range(len(doc)):
        page = doc[page_num]

        # Calcula a matriz de zoom baseado no DPI
        zoom = dpi / 72  # 72 e o DPI padrao do PDF
        mat = fitz.Matrix(zoom, zoom)

        # Renderiza a pagina como imagem
        pix = page.get_pixmap(matrix=mat)

        # Converte para PIL Image
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        imagens.append(img)

    doc.close()

    return imagens


def extrair_texto_ocr(
    pdf_file,
    idioma: str = "por+eng",
    dpi: int = 300
) -> Tuple[str, List[dict], Tuple[float, float]]:
    """
    Extrai texto de um PDF usando OCR (Tesseract).

    Args:
        pdf_file: Arquivo PDF
        idioma: Idioma(s) para OCR (por = portugues, eng = ingles)
        dpi: Resolucao para conversao

    Returns:
        - texto_completo: Todo o texto extraido
        - palavras: Lista de dicts com {text, x0, top, x1, bottom}
        - page_size: Tupla (largura, altura) da pagina original
    """
    if not TESSERACT_DISPONIVEL:
        raise ImportError("pytesseract nao esta instalado. Execute: pip install pytesseract")

    if not verificar_tesseract_instalado():
        # Tenta configurar no Windows
        if sys.platform == 'win32':
            configurar_tesseract_windows()

        if not verificar_tesseract_instalado():
            raise RuntimeError(
                "Tesseract nao esta instalado ou nao foi encontrado.\n"
                "Windows: Baixe de https://github.com/UB-Mannheim/tesseract/wiki\n"
                "Linux: sudo apt-get install tesseract-ocr tesseract-ocr-por\n"
                "Mac: brew install tesseract"
            )

    # Converte PDF para imagens
    imagens = pdf_para_imagens(pdf_file, dpi=dpi)

    if not imagens:
        return "", [], (0, 0)

    # Processa apenas a primeira pagina (POC)
    img = imagens[0]
    img_width, img_height = img.size

    # Obtem dimensoes originais do PDF para escala
    if hasattr(pdf_file, 'read'):
        pdf_file.seek(0)
        pdf_bytes = pdf_file.read()
        pdf_file.seek(0)
    else:
        pdf_bytes = pdf_file

    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    page = doc[0]
    pdf_width = page.rect.width
    pdf_height = page.rect.height
    doc.close()

    # Fatores de escala (imagem -> PDF)
    escala_x = pdf_width / img_width
    escala_y = pdf_height / img_height

    # Executa OCR com dados detalhados
    dados_ocr = pytesseract.image_to_data(
        img,
        lang=idioma,
        output_type=pytesseract.Output.DICT,
        config='--psm 6'  # Assume bloco de texto uniforme
    )

    palavras = []
    texto_linhas = []

    n_boxes = len(dados_ocr['text'])

    for i in range(n_boxes):
        texto = dados_ocr['text'][i].strip()
        conf = int(dados_ocr['conf'][i])

        # Ignora entradas vazias ou com baixa confianca
        if not texto or conf < 30:
            continue

        # Coordenadas na imagem
        x = dados_ocr['left'][i]
        y = dados_ocr['top'][i]
        w = dados_ocr['width'][i]
        h = dados_ocr['height'][i]

        # Converte para coordenadas do PDF
        x0 = x * escala_x
        top = y * escala_y
        x1 = (x + w) * escala_x
        bottom = (y + h) * escala_y

        palavras.append({
            "text": texto,
            "x0": x0,
            "top": top,
            "x1": x1,
            "bottom": bottom,
            "width": x1 - x0,
            "height": bottom - top,
            "confidence": conf
        })

        texto_linhas.append(texto)

    texto_completo = " ".join(texto_linhas)

    return texto_completo, palavras, (pdf_width, pdf_height)


def extrair_texto_pdfplumber(pdf_file) -> Tuple[str, List[dict], Tuple[float, float]]:
    """
    Extrai texto de um PDF usando pdfplumber (para PDFs com texto nativo).

    Returns:
        - texto_completo: Todo o texto extraido
        - palavras: Lista de dicts com {text, x0, top, x1, bottom}
        - page_size: Tupla (largura, altura) da pagina
    """
    if not PDFPLUMBER_DISPONIVEL:
        raise ImportError("pdfplumber nao esta instalado. Execute: pip install pdfplumber")

    palavras = []
    texto_completo = ""

    with pdfplumber.open(pdf_file) as pdf:
        if len(pdf.pages) == 0:
            return "", [], (0, 0)

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


def extrair_texto_automatico(
    pdf_file,
    forcar_ocr: bool = False,
    idioma_ocr: str = "por+eng"
) -> Tuple[str, List[dict], Tuple[float, float], str]:
    """
    Extrai texto de um PDF detectando automaticamente o melhor metodo.

    Args:
        pdf_file: Arquivo PDF
        forcar_ocr: Se True, sempre usa OCR mesmo se tiver texto nativo
        idioma_ocr: Idioma(s) para OCR

    Returns:
        - texto_completo: Todo o texto extraido
        - palavras: Lista de dicts com coordenadas
        - page_size: Tupla (largura, altura)
        - metodo: "pdfplumber" ou "tesseract"
    """
    # Reset do ponteiro se for file-like
    if hasattr(pdf_file, 'seek'):
        pdf_file.seek(0)

    # Verifica se deve usar OCR
    usar_ocr = forcar_ocr

    if not forcar_ocr:
        # Detecta se e escaneado
        if hasattr(pdf_file, 'seek'):
            pdf_file.seek(0)
        usar_ocr = detectar_pdf_escaneado(pdf_file)
        if hasattr(pdf_file, 'seek'):
            pdf_file.seek(0)

    if usar_ocr:
        # Verifica se Tesseract esta disponivel
        if not TESSERACT_DISPONIVEL or not verificar_tesseract_instalado():
            # Fallback para pdfplumber se Tesseract nao disponivel
            if hasattr(pdf_file, 'seek'):
                pdf_file.seek(0)
            texto, palavras, page_size = extrair_texto_pdfplumber(pdf_file)
            return texto, palavras, page_size, "pdfplumber (fallback)"

        if hasattr(pdf_file, 'seek'):
            pdf_file.seek(0)
        texto, palavras, page_size = extrair_texto_ocr(pdf_file, idioma=idioma_ocr)
        return texto, palavras, page_size, "tesseract"
    else:
        if hasattr(pdf_file, 'seek'):
            pdf_file.seek(0)
        texto, palavras, page_size = extrair_texto_pdfplumber(pdf_file)
        return texto, palavras, page_size, "pdfplumber"


# =============================================================================
# TESTE DO MODULO
# =============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("TESTE DO OCR ENGINE")
    print("=" * 60)

    print("\n[1] Verificando dependencias...")
    print(f"    - pytesseract: {'OK' if TESSERACT_DISPONIVEL else 'NAO INSTALADO'}")
    print(f"    - PyMuPDF: {'OK' if PYMUPDF_DISPONIVEL else 'NAO INSTALADO'}")
    print(f"    - pdfplumber: {'OK' if PDFPLUMBER_DISPONIVEL else 'NAO INSTALADO'}")

    if TESSERACT_DISPONIVEL:
        print("\n[2] Verificando Tesseract...")
        if verificar_tesseract_instalado():
            versao = pytesseract.get_tesseract_version()
            print(f"    - Tesseract instalado: v{versao}")
        else:
            print("    - Tesseract NAO encontrado no sistema")
            print("    - Windows: Baixe de https://github.com/UB-Mannheim/tesseract/wiki")

    print("\n" + "=" * 60)
