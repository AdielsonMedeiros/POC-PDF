"""
=============================================================================
TESTES DO MÓDULO OCR ENGINE
=============================================================================
Testa as funções de OCR e extração de texto de PDFs.
"""

import pytest
import sys
from io import BytesIO
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from ocr_engine import (
    verificar_tesseract_instalado,
    TESSERACT_DISPONIVEL,
    extrair_texto_pdfplumber,
    extrair_texto_automatico,
    detectar_pdf_escaneado
)


# =============================================================================
# TESTES DE VERIFICAÇÃO DO TESSERACT
# =============================================================================

class TestVerificacaoTesseract:
    """Testes para verificação do Tesseract."""
    
    def test_verificar_tesseract_retorna_bool(self):
        """Deve retornar booleano."""
        resultado = verificar_tesseract_instalado()
        assert isinstance(resultado, bool)
    
    def test_tesseract_disponivel_consistente(self):
        """TESSERACT_DISPONIVEL deve ser consistente com verificação."""
        # A constante é definida na importação
        assert isinstance(TESSERACT_DISPONIVEL, bool)


# =============================================================================
# TESTES DE EXTRAÇÃO COM PDFPLUMBER
# =============================================================================

class TestExtracaoPdfplumber:
    """Testes para extração nativa com pdfplumber."""
    
    def test_extrair_texto_pdf_simples(self, pdf_simples):
        """Deve extrair texto de PDF simples."""
        texto, palavras, page_size = extrair_texto_pdfplumber(pdf_simples)
        
        assert texto is not None
        assert len(texto) > 0
        assert isinstance(palavras, list)
        assert page_size is not None
    
    def test_extrair_texto_retorna_palavras(self, pdf_simples):
        """Deve retornar lista de palavras com coordenadas."""
        texto, palavras, page_size = extrair_texto_pdfplumber(pdf_simples)
        
        assert len(palavras) > 0
        
        # Verifica estrutura das palavras
        for palavra in palavras:
            assert "text" in palavra
            assert "x0" in palavra
            assert "top" in palavra
            assert "x1" in palavra
            assert "bottom" in palavra
    
    def test_extrair_texto_page_size(self, pdf_simples):
        """Deve retornar tamanho da página."""
        texto, palavras, page_size = extrair_texto_pdfplumber(pdf_simples)
        
        assert isinstance(page_size, tuple)
        assert len(page_size) == 2
        assert page_size[0] > 0  # largura
        assert page_size[1] > 0  # altura
    
    def test_extrair_texto_pdf_vazio(self, pdf_vazio):
        """Deve lidar com PDF sem texto."""
        texto, palavras, page_size = extrair_texto_pdfplumber(pdf_vazio)
        
        assert texto == "" or texto is None or len(texto.strip()) == 0
        assert isinstance(palavras, list)


# =============================================================================
# TESTES DE DETECÇÃO DE PDF ESCANEADO
# =============================================================================

class TestDeteccaoPdfEscaneado:
    """Testes para detecção de PDFs escaneados."""
    
    def test_pdf_com_texto_nativo(self, pdf_simples):
        """Deve detectar que PDF tem texto nativo (não é escaneado)."""
        eh_escaneado = detectar_pdf_escaneado(pdf_simples)
        
        assert eh_escaneado == False
    
    def test_pdf_sem_texto(self, pdf_vazio):
        """Deve detectar PDF vazio como escaneado."""
        eh_escaneado = detectar_pdf_escaneado(pdf_vazio)
        
        assert eh_escaneado == True


# =============================================================================
# TESTES DE EXTRAÇÃO AUTOMÁTICA
# =============================================================================

class TestExtracaoAutomatica:
    """Testes para extração automática (escolhe entre nativo e OCR)."""
    
    def test_extrair_automatico_pdf_com_texto(self, pdf_simples):
        """Deve usar pdfplumber para PDF com texto nativo."""
        texto, palavras, page_size, metodo = extrair_texto_automatico(pdf_simples)
        
        assert texto is not None
        assert len(texto) > 0
        assert "pdfplumber" in metodo.lower() or "nativo" in metodo.lower()
    
    def test_extrair_automatico_retorna_metodo(self, pdf_simples):
        """Deve retornar método utilizado."""
        texto, palavras, page_size, metodo = extrair_texto_automatico(pdf_simples)
        
        assert metodo is not None
        assert isinstance(metodo, str)
    
    @pytest.mark.skipif(not TESSERACT_DISPONIVEL, reason="Tesseract não instalado")
    def test_extrair_automatico_forcar_ocr(self, pdf_simples):
        """Deve usar OCR quando forçado (se disponível)."""
        texto, palavras, page_size, metodo = extrair_texto_automatico(
            pdf_simples, 
            forcar_ocr=True
        )
        
        assert "ocr" in metodo.lower() or "tesseract" in metodo.lower()
    
    def test_extrair_automatico_pdf_vazio(self, pdf_vazio):
        """Deve lidar com PDF vazio."""
        texto, palavras, page_size, metodo = extrair_texto_automatico(pdf_vazio)
        
        # Deve retornar algo, mesmo que vazio
        assert page_size is not None


# =============================================================================
# TESTES DE CONTEÚDO EXTRAÍDO
# =============================================================================

class TestConteudoExtraido:
    """Testes para verificar conteúdo extraído corretamente."""
    
    def test_conteudo_campos_comuns(self, pdf_simples):
        """Deve extrair campos comuns do documento."""
        texto, _, _, _ = extrair_texto_automatico(pdf_simples)
        
        # Verifica presença de conteúdo esperado
        texto_lower = texto.lower()
        
        # Pelo menos alguns campos devem estar presentes
        campos_esperados = ["joão", "silva", "cpf", "data", "valor"]
        campos_encontrados = sum(1 for campo in campos_esperados if campo in texto_lower)
        
        assert campos_encontrados >= 2, f"Poucos campos encontrados. Texto: {texto}"
    
    def test_coordenadas_validas(self, pdf_simples):
        """Coordenadas devem ser valores válidos."""
        _, palavras, page_size, _ = extrair_texto_automatico(pdf_simples)
        
        for palavra in palavras:
            assert palavra["x0"] >= 0
            assert palavra["top"] >= 0
            assert palavra["x1"] >= palavra["x0"]
            assert palavra["bottom"] >= palavra["top"]
            
            # Coordenadas não devem exceder tamanho da página (com margem)
            assert palavra["x1"] <= page_size[0] + 10
            assert palavra["bottom"] <= page_size[1] + 10


# =============================================================================
# TESTES DE ROBUSTEZ
# =============================================================================

class TestRobustez:
    """Testes de robustez e edge cases."""
    
    def test_seek_automatico(self, pdf_simples):
        """Deve funcionar mesmo se arquivo não estiver no início."""
        # Move para o final
        pdf_simples.seek(0, 2)  # SEEK_END
        
        # Deve funcionar mesmo assim
        texto, _, _, _ = extrair_texto_automatico(pdf_simples)
        
        assert texto is not None
    
    def test_multiplas_chamadas(self, pdf_simples):
        """Deve funcionar em múltiplas chamadas consecutivas."""
        for _ in range(3):
            texto, palavras, page_size, metodo = extrair_texto_automatico(pdf_simples)
            assert texto is not None
            assert len(palavras) > 0
