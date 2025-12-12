"""
=============================================================================
TESTES DE INTEGRAÇÃO E CENÁRIOS REAIS
=============================================================================
Testes de integração para aumentar ainda mais a cobertura.
"""

import pytest
import sys
from io import BytesIO
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


# =============================================================================
# TESTES DE OCR COM PDF (se Tesseract disponível)
# =============================================================================

class TestOCRComPdf:
    """Testes de OCR com PDFs."""
    
    def test_extrair_texto_ocr_pdf_simples(self, pdf_simples):
        """Deve extrair texto com OCR de PDF."""
        from ocr_engine import extrair_texto_ocr, TESSERACT_DISPONIVEL
        
        if not TESSERACT_DISPONIVEL:
            pytest.skip("Tesseract não instalado")
        
        texto, palavras, page_size = extrair_texto_ocr(pdf_simples)
        
        assert texto is not None
        assert isinstance(palavras, list)
        assert page_size is not None
    
    def test_pdf_para_imagens(self, pdf_simples):
        """Deve converter PDF para imagens."""
        from ocr_engine import pdf_para_imagens, PYMUPDF_DISPONIVEL
        
        if not PYMUPDF_DISPONIVEL:
            pytest.skip("PyMuPDF não instalado")
        
        imagens = pdf_para_imagens(pdf_simples)
        
        assert imagens is not None
        assert len(imagens) > 0


# =============================================================================
# TESTES DE FLUXO COMPLETO
# =============================================================================

class TestFluxoCompleto:
    """Testes de fluxo completo da aplicação."""
    
    def test_fluxo_pdf_para_template(self, pdf_simples):
        """Testa fluxo completo: PDF -> extração -> template -> salvamento."""
        from conversor import extrair_texto_documento
        from database import salvar_template, carregar_template, deletar_template
        from tests.test_app import calcular_hash_documento
        
        # 1. Calcula hash
        hash_doc = calcular_hash_documento(pdf_simples)
        assert len(hash_doc) == 16
        
        # 2. Extrai texto
        pdf_simples.seek(0)
        texto, palavras, page_size, metodo = extrair_texto_documento(pdf_simples, "doc.pdf")
        assert len(texto) > 0
        
        # 3. Cria mapeamentos simulados
        mapeamentos = []
        if len(palavras) > 0:
            mapeamentos.append({
                "tipo": "CAMPO_TESTE",
                "descricao": "Campo de Teste",
                "texto_original": palavras[0]["text"],
                "x0": palavras[0]["x0"],
                "top": palavras[0]["top"],
                "x1": palavras[0]["x1"],
                "bottom": palavras[0]["bottom"]
            })
        
        # 4. Salva template
        template_id = salvar_template(hash_doc, mapeamentos)
        assert template_id is not None
        
        # 5. Carrega template
        resultado = carregar_template(hash_doc)
        assert resultado is not None
        assert len(resultado) == len(mapeamentos)
        
        # 6. Limpa
        deletar_template(hash_doc)
    
    def test_fluxo_imagem_para_pdf(self, imagem_jpg):
        """Testa fluxo: imagem -> conversão -> PDF válido."""
        from conversor import processar_documento, PIL_DISPONIVEL, PYMUPDF_DISPONIVEL
        
        if not PIL_DISPONIVEL or not PYMUPDF_DISPONIVEL:
            pytest.skip("Dependências não instaladas")
        
        pdf_result, tipo, convertido = processar_documento(imagem_jpg, "foto.jpg")
        
        assert convertido == True
        assert tipo == "Imagem"
        
        pdf_result.seek(0)
        assert pdf_result.read(4) == b'%PDF'
    
    def test_fluxo_word_para_pdf(self, docx_simples):
        """Testa fluxo: Word -> conversão -> PDF válido."""
        from conversor import processar_documento, DOCX_DISPONIVEL, PYMUPDF_DISPONIVEL
        
        if not DOCX_DISPONIVEL or not PYMUPDF_DISPONIVEL:
            pytest.skip("Dependências não instaladas")
        
        pdf_result, tipo, convertido = processar_documento(docx_simples, "contrato.docx")
        
        assert convertido == True
        assert tipo == "Word"
        
        pdf_result.seek(0)
        assert pdf_result.read(4) == b'%PDF'


# =============================================================================
# TESTES DE BANCO DE DADOS COMPLETOS
# =============================================================================

class TestDatabaseCompleto:
    """Testes completos do banco de dados."""
    
    def test_ciclo_vida_template_completo(self):
        """Testa ciclo completo: criar -> atualizar -> listar -> deletar."""
        from database import (
            salvar_template, carregar_template, 
            listar_templates, deletar_template,
            template_existe, contar_templates
        )
        
        hash_test = "test_lifecycle_hash"
        
        # Garante que não existe
        deletar_template(hash_test)
        assert template_existe(hash_test) == False
        
        count_inicial = contar_templates()
        
        # Cria
        mapeamentos_v1 = [{"tipo": "V1", "descricao": "Versão 1", "texto_original": "val1", "x0": 0, "top": 0, "x1": 10, "bottom": 10}]
        id1 = salvar_template(hash_test, mapeamentos_v1)
        
        assert template_existe(hash_test) == True
        assert contar_templates() == count_inicial + 1
        
        # Atualiza
        mapeamentos_v2 = [
            {"tipo": "V2A", "descricao": "Versão 2A", "texto_original": "val2a", "x0": 0, "top": 0, "x1": 10, "bottom": 10},
            {"tipo": "V2B", "descricao": "Versão 2B", "texto_original": "val2b", "x0": 20, "top": 0, "x1": 30, "bottom": 10}
        ]
        id2 = salvar_template(hash_test, mapeamentos_v2)
        
        # ID deve ser o mesmo (update)
        assert id1 == id2
        
        # Verifica que mapeamentos foram atualizados
        resultado = carregar_template(hash_test)
        assert len(resultado) == 2
        
        # Lista deve conter o template
        lista = listar_templates()
        hashes = [t['hash'] for t in lista]
        assert hash_test in hashes
        
        # Deleta
        sucesso = deletar_template(hash_test)
        assert sucesso == True
        assert template_existe(hash_test) == False
    
    def test_multiplos_templates(self):
        """Testa operações com múltiplos templates."""
        from database import salvar_template, listar_templates, deletar_template, contar_templates
        
        hashes = [f"multi_test_{i}" for i in range(5)]
        
        # Limpa antes
        for h in hashes:
            deletar_template(h)
        
        count_inicial = contar_templates()
        
        # Cria vários
        for h in hashes:
            salvar_template(h, [{"tipo": f"TIPO_{h}", "descricao": "Desc", "texto_original": "val", "x0": 0, "top": 0, "x1": 10, "bottom": 10}])
        
        assert contar_templates() == count_inicial + 5
        
        # Lista todos
        lista = listar_templates()
        hashes_encontrados = [t['hash'] for t in lista]
        
        for h in hashes:
            assert h in hashes_encontrados
        
        # Limpa
        for h in hashes:
            deletar_template(h)


# =============================================================================
# TESTES DE CONSTANTES E IMPORTS
# =============================================================================

class TestConstantesImports:
    """Testes de constantes e importações."""
    
    def test_constantes_conversor(self):
        """Verifica constantes do conversor."""
        from conversor import (
            FORMATOS_PDF, FORMATOS_IMAGEM, FORMATOS_WORD, TODOS_FORMATOS,
            PIL_DISPONIVEL, PYMUPDF_DISPONIVEL, DOCX_DISPONIVEL
        )
        
        assert isinstance(FORMATOS_PDF, list)
        assert isinstance(FORMATOS_IMAGEM, list)
        assert isinstance(FORMATOS_WORD, list)
        assert len(TODOS_FORMATOS) == len(FORMATOS_PDF) + len(FORMATOS_IMAGEM) + len(FORMATOS_WORD)
        
        assert isinstance(PIL_DISPONIVEL, bool)
        assert isinstance(PYMUPDF_DISPONIVEL, bool)
        assert isinstance(DOCX_DISPONIVEL, bool)
    
    def test_constantes_database(self):
        """Verifica constantes do database."""
        from database import (
            DATA_DIR, SQLITE_DB, CHROMA_DIR,
            CHROMADB_DISPONIVEL, LIMIAR_SIMILARIDADE
        )
        
        assert isinstance(DATA_DIR, Path)
        assert isinstance(SQLITE_DB, Path)
        assert isinstance(CHROMA_DIR, Path)
        assert isinstance(CHROMADB_DISPONIVEL, bool)
        assert isinstance(LIMIAR_SIMILARIDADE, float)
        assert 0 <= LIMIAR_SIMILARIDADE <= 1
    
    def test_constantes_ocr(self):
        """Verifica constantes do OCR engine."""
        from ocr_engine import (
            TESSERACT_DISPONIVEL,
            PYMUPDF_DISPONIVEL,
            PDFPLUMBER_DISPONIVEL
        )
        
        assert isinstance(TESSERACT_DISPONIVEL, bool)
        assert isinstance(PYMUPDF_DISPONIVEL, bool)
        assert isinstance(PDFPLUMBER_DISPONIVEL, bool)


# =============================================================================
# TESTES DE ERROS E EXCEÇÕES
# =============================================================================

class TestErrosExcecoes:
    """Testes de tratamento de erros."""
    
    def test_formato_nao_suportado_processar(self, pdf_simples):
        """Deve lançar ValueError para formato não suportado."""
        from conversor import processar_documento
        
        with pytest.raises(ValueError) as exc:
            processar_documento(pdf_simples, "arquivo.xyz")
        
        assert "nao suportado" in str(exc.value).lower()
    
    def test_formato_nao_suportado_extrair(self, pdf_simples):
        """Deve lançar ValueError para formato não suportado na extração."""
        from conversor import extrair_texto_documento
        
        with pytest.raises(ValueError) as exc:
            extrair_texto_documento(pdf_simples, "arquivo.mp3")
        
        assert "nao suportado" in str(exc.value).lower()
    
    def test_carregar_template_inexistente(self):
        """Deve retornar None para template inexistente."""
        from database import carregar_template
        
        resultado = carregar_template("hash_absolutamente_inexistente_123456789")
        
        assert resultado is None


# =============================================================================
# TESTES DE DOCX COM TABELAS E PARÁGRAFOS
# =============================================================================

class TestDocxAvancado:
    """Testes avançados de documentos Word."""
    
    def test_docx_paragrafos_e_tabelas(self, docx_simples):
        """Deve extrair texto de parágrafos e tabelas."""
        from conversor import extrair_texto_docx, DOCX_DISPONIVEL
        
        if not DOCX_DISPONIVEL:
            pytest.skip("python-docx não instalado")
        
        texto, palavras, page_size = extrair_texto_docx(docx_simples)
        
        # Verifica texto dos parágrafos
        assert "Pedro Oliveira" in texto
        assert "111.222.333-44" in texto
        
        # Verifica texto da tabela
        assert "Serviço A" in texto or "Item" in texto
    
    def test_docx_coordenadas_simuladas(self, docx_simples):
        """Deve gerar coordenadas simuladas para palavras."""
        from conversor import extrair_texto_docx, DOCX_DISPONIVEL
        
        if not DOCX_DISPONIVEL:
            pytest.skip("python-docx não instalado")
        
        texto, palavras, page_size = extrair_texto_docx(docx_simples)
        
        # Todas as palavras devem ter coordenadas válidas
        for palavra in palavras:
            assert palavra["x0"] >= 0
            assert palavra["top"] >= 0
            assert palavra["x1"] > palavra["x0"]
            assert palavra["bottom"] > palavra["top"]
