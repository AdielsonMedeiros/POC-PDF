"""
=============================================================================
TESTES DO MÓDULO CONVERSOR
=============================================================================
Testa as funções de detecção de formato e conversão de documentos.
"""

import pytest
import sys
from io import BytesIO
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from conversor import (
    get_extensao,
    eh_pdf,
    eh_imagem,
    eh_word,
    formato_suportado,
    imagem_para_pdf,
    extrair_texto_docx,
    docx_para_pdf,
    processar_documento,
    extrair_texto_documento,
    FORMATOS_PDF,
    FORMATOS_IMAGEM,
    FORMATOS_WORD,
    TODOS_FORMATOS,
    PIL_DISPONIVEL,
    PYMUPDF_DISPONIVEL,
    DOCX_DISPONIVEL
)


# =============================================================================
# TESTES DE DETECÇÃO DE FORMATO
# =============================================================================

class TestDeteccaoFormato:
    """Testes para funções de detecção de tipo de arquivo."""
    
    def test_get_extensao_minusculo(self):
        """Deve retornar extensão em minúsculo."""
        assert get_extensao("arquivo.PDF") == ".pdf"
        assert get_extensao("arquivo.Docx") == ".docx"
        assert get_extensao("arquivo.JPG") == ".jpg"
    
    def test_get_extensao_sem_extensao(self):
        """Deve retornar string vazia para arquivos sem extensão."""
        assert get_extensao("arquivo") == ""
    
    def test_get_extensao_multiplos_pontos(self):
        """Deve retornar apenas a última extensão."""
        assert get_extensao("arquivo.teste.pdf") == ".pdf"
    
    def test_eh_pdf_valido(self):
        """Deve identificar PDFs corretamente."""
        assert eh_pdf("documento.pdf") == True
        assert eh_pdf("DOCUMENTO.PDF") == True
        assert eh_pdf("arquivo.PDF") == True
    
    def test_eh_pdf_invalido(self):
        """Não deve identificar outros formatos como PDF."""
        assert eh_pdf("documento.docx") == False
        assert eh_pdf("imagem.png") == False
        assert eh_pdf("arquivo") == False
    
    def test_eh_imagem_valido(self):
        """Deve identificar imagens corretamente."""
        for ext in ['png', 'jpg', 'jpeg', 'bmp', 'tiff', 'tif']:
            assert eh_imagem(f"imagem.{ext}") == True
            assert eh_imagem(f"IMAGEM.{ext.upper()}") == True
    
    def test_eh_imagem_invalido(self):
        """Não deve identificar outros formatos como imagem."""
        assert eh_imagem("documento.pdf") == False
        assert eh_imagem("arquivo.docx") == False
        assert eh_imagem("video.mp4") == False
    
    def test_eh_word_valido(self):
        """Deve identificar documentos Word corretamente."""
        assert eh_word("documento.docx") == True
        assert eh_word("arquivo.doc") == True
        assert eh_word("CONTRATO.DOCX") == True
    
    def test_eh_word_invalido(self):
        """Não deve identificar outros formatos como Word."""
        assert eh_word("documento.pdf") == False
        assert eh_word("imagem.png") == False
    
    def test_formato_suportado_valido(self):
        """Deve identificar todos os formatos suportados."""
        formatos_validos = [
            "arquivo.pdf", "imagem.png", "foto.jpg", 
            "documento.docx", "contrato.doc", "scan.tiff"
        ]
        for arquivo in formatos_validos:
            assert formato_suportado(arquivo) == True, f"{arquivo} deveria ser suportado"
    
    def test_formato_suportado_invalido(self):
        """Não deve aceitar formatos não suportados."""
        formatos_invalidos = [
            "video.mp4", "audio.mp3", "arquivo.txt",
            "planilha.xlsx", "apresentacao.pptx"
        ]
        for arquivo in formatos_invalidos:
            assert formato_suportado(arquivo) == False, f"{arquivo} não deveria ser suportado"


# =============================================================================
# TESTES DE CONVERSÃO DE IMAGEM
# =============================================================================

class TestConversaoImagem:
    """Testes para conversão de imagens para PDF."""
    
    @pytest.mark.skipif(not PIL_DISPONIVEL, reason="Pillow não instalado")
    @pytest.mark.skipif(not PYMUPDF_DISPONIVEL, reason="PyMuPDF não instalado")
    def test_imagem_png_para_pdf(self, imagem_com_texto):
        """Deve converter PNG para PDF."""
        pdf_result = imagem_para_pdf(imagem_com_texto, "teste.png")
        
        assert pdf_result is not None
        assert isinstance(pdf_result, BytesIO)
        
        # Verifica que é um PDF válido (começa com %PDF)
        pdf_result.seek(0)
        header = pdf_result.read(4)
        assert header == b'%PDF'
    
    @pytest.mark.skipif(not PIL_DISPONIVEL, reason="Pillow não instalado")
    @pytest.mark.skipif(not PYMUPDF_DISPONIVEL, reason="PyMuPDF não instalado")
    def test_imagem_jpg_para_pdf(self, imagem_jpg):
        """Deve converter JPG para PDF."""
        pdf_result = imagem_para_pdf(imagem_jpg, "teste.jpg")
        
        assert pdf_result is not None
        pdf_result.seek(0)
        header = pdf_result.read(4)
        assert header == b'%PDF'
    
    @pytest.mark.skipif(not PIL_DISPONIVEL, reason="Pillow não instalado")
    @pytest.mark.skipif(not PYMUPDF_DISPONIVEL, reason="PyMuPDF não instalado")
    def test_imagem_bmp_para_pdf(self, imagem_bmp):
        """Deve converter BMP para PDF."""
        pdf_result = imagem_para_pdf(imagem_bmp, "teste.bmp")
        
        assert pdf_result is not None
        pdf_result.seek(0)
        header = pdf_result.read(4)
        assert header == b'%PDF'
    
    @pytest.mark.skipif(not PIL_DISPONIVEL, reason="Pillow não instalado")
    @pytest.mark.skipif(not PYMUPDF_DISPONIVEL, reason="PyMuPDF não instalado")
    def test_imagem_rgba_para_pdf(self):
        """Deve converter imagem com transparência para PDF."""
        from PIL import Image
        
        # Cria imagem RGBA (com alpha)
        img = Image.new('RGBA', (200, 200), color=(255, 0, 0, 128))
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        
        pdf_result = imagem_para_pdf(buffer, "transparente.png")
        
        assert pdf_result is not None
        pdf_result.seek(0)
        header = pdf_result.read(4)
        assert header == b'%PDF'


# =============================================================================
# TESTES DE CONVERSÃO DE WORD
# =============================================================================

class TestConversaoWord:
    """Testes para extração de texto e conversão de documentos Word."""
    
    @pytest.mark.skipif(not DOCX_DISPONIVEL, reason="python-docx não instalado")
    def test_extrair_texto_docx(self, docx_simples):
        """Deve extrair texto de documento DOCX."""
        texto, palavras, page_size = extrair_texto_docx(docx_simples)
        
        assert texto is not None
        assert len(texto) > 0
        assert "Pedro Oliveira" in texto
        assert "111.222.333-44" in texto
        assert "R$ 5.000,00" in texto
    
    @pytest.mark.skipif(not DOCX_DISPONIVEL, reason="python-docx não instalado")
    def test_extrair_texto_docx_retorna_palavras(self, docx_simples):
        """Deve retornar lista de palavras com coordenadas simuladas."""
        texto, palavras, page_size = extrair_texto_docx(docx_simples)
        
        assert isinstance(palavras, list)
        assert len(palavras) > 0
        
        # Verifica estrutura das palavras
        for palavra in palavras:
            assert "text" in palavra
            assert "x0" in palavra
            assert "top" in palavra
            assert "x1" in palavra
            assert "bottom" in palavra
    
    @pytest.mark.skipif(not DOCX_DISPONIVEL, reason="python-docx não instalado")
    def test_extrair_texto_docx_page_size(self, docx_simples):
        """Deve retornar tamanho de página A4."""
        texto, palavras, page_size = extrair_texto_docx(docx_simples)
        
        assert page_size == (595, 842)  # A4 em pontos
    
    @pytest.mark.skipif(not DOCX_DISPONIVEL, reason="python-docx não instalado")
    @pytest.mark.skipif(not PYMUPDF_DISPONIVEL, reason="PyMuPDF não instalado")
    def test_docx_para_pdf(self, docx_simples):
        """Deve converter DOCX para PDF."""
        pdf_result = docx_para_pdf(docx_simples)
        
        assert pdf_result is not None
        pdf_result.seek(0)
        header = pdf_result.read(4)
        assert header == b'%PDF'


# =============================================================================
# TESTES DE PROCESSAMENTO UNIFICADO
# =============================================================================

class TestProcessarDocumento:
    """Testes para a função principal de processamento."""
    
    def test_processar_pdf(self, pdf_simples):
        """Deve processar PDF sem conversão."""
        pdf_result, tipo, convertido = processar_documento(pdf_simples, "documento.pdf")
        
        assert pdf_result is not None
        assert tipo == "PDF"
        assert convertido == False
    
    @pytest.mark.skipif(not PIL_DISPONIVEL, reason="Pillow não instalado")
    @pytest.mark.skipif(not PYMUPDF_DISPONIVEL, reason="PyMuPDF não instalado")
    def test_processar_imagem(self, imagem_com_texto):
        """Deve processar e converter imagem para PDF."""
        pdf_result, tipo, convertido = processar_documento(imagem_com_texto, "scan.png")
        
        assert pdf_result is not None
        assert tipo == "Imagem"
        assert convertido == True
        
        # Verifica que é PDF
        pdf_result.seek(0)
        header = pdf_result.read(4)
        assert header == b'%PDF'
    
    @pytest.mark.skipif(not DOCX_DISPONIVEL, reason="python-docx não instalado")
    @pytest.mark.skipif(not PYMUPDF_DISPONIVEL, reason="PyMuPDF não instalado")
    def test_processar_word(self, docx_simples):
        """Deve processar e converter Word para PDF."""
        pdf_result, tipo, convertido = processar_documento(docx_simples, "contrato.docx")
        
        assert pdf_result is not None
        assert tipo == "Word"
        assert convertido == True
        
        # Verifica que é PDF
        pdf_result.seek(0)
        header = pdf_result.read(4)
        assert header == b'%PDF'
    
    def test_processar_formato_invalido(self, pdf_simples):
        """Deve lançar erro para formato não suportado."""
        with pytest.raises(ValueError) as excinfo:
            processar_documento(pdf_simples, "video.mp4")
        
        assert "nao suportado" in str(excinfo.value).lower()


# =============================================================================
# TESTES DE EXTRAÇÃO DE TEXTO UNIFICADA
# =============================================================================

class TestExtrairTextoDocumento:
    """Testes para extração de texto de qualquer formato."""
    
    def test_extrair_texto_pdf(self, pdf_simples):
        """Deve extrair texto de PDF."""
        texto, palavras, page_size, metodo = extrair_texto_documento(
            pdf_simples, "documento.pdf"
        )
        
        assert texto is not None
        assert len(texto) > 0
        assert "João" in texto or "Silva" in texto
        assert page_size is not None
        assert metodo is not None
    
    @pytest.mark.skipif(not DOCX_DISPONIVEL, reason="python-docx não instalado")
    def test_extrair_texto_word(self, docx_simples):
        """Deve extrair texto de Word."""
        texto, palavras, page_size, metodo = extrair_texto_documento(
            docx_simples, "contrato.docx"
        )
        
        assert texto is not None
        assert "Pedro Oliveira" in texto
        assert metodo == "Word (texto)"
    
    def test_extrair_texto_formato_invalido(self, pdf_simples):
        """Deve lançar erro para formato não suportado."""
        with pytest.raises(ValueError):
            extrair_texto_documento(pdf_simples, "arquivo.xyz")


# =============================================================================
# TESTES DE CONSTANTES
# =============================================================================

class TestConstantes:
    """Testes para verificar as constantes do módulo."""
    
    def test_formatos_pdf(self):
        """Deve ter extensão PDF."""
        assert ".pdf" in FORMATOS_PDF
    
    def test_formatos_imagem(self):
        """Deve ter principais formatos de imagem."""
        assert ".png" in FORMATOS_IMAGEM
        assert ".jpg" in FORMATOS_IMAGEM
        assert ".jpeg" in FORMATOS_IMAGEM
        assert ".tiff" in FORMATOS_IMAGEM
    
    def test_formatos_word(self):
        """Deve ter formatos Word."""
        assert ".docx" in FORMATOS_WORD
        assert ".doc" in FORMATOS_WORD
    
    def test_todos_formatos(self):
        """Deve conter todos os formatos combinados."""
        assert len(TODOS_FORMATOS) == len(FORMATOS_PDF) + len(FORMATOS_IMAGEM) + len(FORMATOS_WORD)
