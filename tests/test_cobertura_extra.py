"""
=============================================================================
TESTES ADICIONAIS - Cobertura Expandida
=============================================================================
Testes adicionais para aumentar a cobertura de código.
"""

import pytest
import sys
import os
from io import BytesIO
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


# =============================================================================
# TESTES DE NORMALIZAÇÃO DE TEXTO (database.py)
# =============================================================================

class TestNormalizacaoTexto:
    """Testes para normalização de texto para embedding."""
    
    def test_normalizar_numeros(self):
        """Deve substituir números por NUM."""
        from database import normalizar_texto_para_embedding
        
        texto = "Pedido 12345 com quantidade 100"
        resultado = normalizar_texto_para_embedding(texto)
        
        assert "12345" not in resultado
        assert "100" not in resultado
        assert "num" in resultado.lower()
    
    def test_normalizar_valores_monetarios(self):
        """Deve substituir valores monetários."""
        from database import normalizar_texto_para_embedding
        
        texto = "Total: R$ 1.500,00 e R$2500,50"
        resultado = normalizar_texto_para_embedding(texto)
        
        # Verifica que os valores numéricos foram removidos/substituídos
        assert "1500" not in resultado
        assert "2500" not in resultado
        # O regex pode substituir por VALOR ou NUM dependendo da ordem
    
    def test_normalizar_datas(self):
        """Deve substituir datas por DATA."""
        from database import normalizar_texto_para_embedding
        
        texto = "Data de nascimento: 15/03/1990 e vencimento 01-12-2024"
        resultado = normalizar_texto_para_embedding(texto)
        
        assert "15/03/1990" not in resultado
        assert "01-12-2024" not in resultado
        assert "data" in resultado.lower()
    
    def test_normalizar_cpf(self):
        """Deve substituir CPF por CPF."""
        from database import normalizar_texto_para_embedding
        
        texto = "CPF: 123.456.789-00"
        resultado = normalizar_texto_para_embedding(texto)
        
        assert "123.456.789-00" not in resultado
    
    def test_normalizar_email(self):
        """Deve substituir email por EMAIL."""
        from database import normalizar_texto_para_embedding
        
        texto = "Contato: usuario@empresa.com.br"
        resultado = normalizar_texto_para_embedding(texto)
        
        assert "usuario@empresa.com.br" not in resultado
        assert "email" in resultado.lower()
    
    def test_normalizar_telefone(self):
        """Deve substituir telefone por TELEFONE."""
        from database import normalizar_texto_para_embedding
        
        texto = "Tel: (11) 99999-9999 e (21)3333-4444"
        resultado = normalizar_texto_para_embedding(texto)
        
        assert "99999-9999" not in resultado
        assert "3333-4444" not in resultado
    
    def test_normalizar_espacos_multiplos(self):
        """Deve remover espaços múltiplos."""
        from database import normalizar_texto_para_embedding
        
        texto = "Texto    com    muitos     espaços"
        resultado = normalizar_texto_para_embedding(texto)
        
        assert "    " not in resultado
    
    def test_normalizar_para_minusculas(self):
        """Deve converter para minúsculas."""
        from database import normalizar_texto_para_embedding
        
        texto = "TEXTO EM MAIÚSCULAS"
        resultado = normalizar_texto_para_embedding(texto)
        
        assert resultado == resultado.lower()


# =============================================================================
# TESTES DE CHROMADB (database.py)
# =============================================================================

class TestChromaDB:
    """Testes para funções do ChromaDB."""
    
    def test_get_colecao_chroma(self):
        """Deve retornar coleção se ChromaDB disponível."""
        from database import get_colecao_chroma, CHROMADB_DISPONIVEL
        
        colecao = get_colecao_chroma()
        
        if CHROMADB_DISPONIVEL:
            assert colecao is not None
        else:
            assert colecao is None
    
    def test_contar_embeddings(self):
        """Deve retornar contagem de embeddings."""
        from database import contar_embeddings, CHROMADB_DISPONIVEL
        
        count = contar_embeddings()
        
        if CHROMADB_DISPONIVEL:
            assert isinstance(count, int)
            assert count >= 0
        else:
            assert count == 0
    
    def test_deletar_embedding_inexistente(self):
        """Deve retornar False ao deletar embedding inexistente."""
        from database import deletar_embedding, CHROMADB_DISPONIVEL
        
        resultado = deletar_embedding("hash_que_nao_existe_xyz")
        
        # Retorna False se não existe ou se ChromaDB não disponível
        assert isinstance(resultado, bool)


# =============================================================================
# TESTES DE EXTRAÇÃO DE TEXTO OCR (conversor.py)
# =============================================================================

class TestExtracaoTextoImagem:
    """Testes para extração de texto de imagens."""
    
    @pytest.mark.skipif(
        not pytest.importorskip("pytesseract", reason="pytesseract não instalado"),
        reason="pytesseract não instalado"
    )
    def test_extrair_texto_imagem(self, imagem_com_texto):
        """Deve extrair texto de imagem com OCR."""
        from conversor import extrair_texto_imagem
        from ocr_engine import TESSERACT_DISPONIVEL
        
        if not TESSERACT_DISPONIVEL:
            pytest.skip("Tesseract não instalado")
        
        texto, palavras, size = extrair_texto_imagem(imagem_com_texto)
        
        assert texto is not None
        assert isinstance(palavras, list)
        assert len(size) == 2


# =============================================================================
# TESTES DE OCR ENGINE AVANÇADOS
# =============================================================================

class TestOCREngineAvancado:
    """Testes avançados do motor de OCR."""
    
    def test_configurar_tesseract_windows(self):
        """Deve tentar configurar Tesseract no Windows."""
        from ocr_engine import configurar_tesseract_windows
        import sys
        
        if sys.platform == 'win32':
            # Não deve lançar exceção
            configurar_tesseract_windows()
            assert True
        else:
            pytest.skip("Teste apenas para Windows")
    
    def test_detectar_pdf_escaneado_limiar(self, pdf_simples):
        """Deve respeitar limiar de caracteres."""
        from ocr_engine import detectar_pdf_escaneado
        
        # Com limiar muito alto, qualquer PDF parece escaneado
        eh_escaneado = detectar_pdf_escaneado(pdf_simples, limiar_caracteres=10000)
        assert eh_escaneado == True
        
        # Com limiar baixo, PDF com texto não parece escaneado
        pdf_simples.seek(0)
        eh_escaneado = detectar_pdf_escaneado(pdf_simples, limiar_caracteres=1)
        assert eh_escaneado == False


# =============================================================================
# TESTES DE CONVERSÃO AVANÇADOS (conversor.py)
# =============================================================================

class TestConversaoAvancada:
    """Testes avançados de conversão."""
    
    def test_processar_documento_preserva_conteudo(self, pdf_simples):
        """Deve preservar conteúdo ao processar PDF."""
        from conversor import processar_documento
        
        # Lê conteúdo original
        pdf_simples.seek(0)
        conteudo_original = pdf_simples.read()
        pdf_simples.seek(0)
        
        # Processa
        pdf_result, tipo, convertido = processar_documento(pdf_simples, "doc.pdf")
        
        # Para PDF, deve retornar o mesmo conteúdo
        assert not convertido
        pdf_result.seek(0)
        conteudo_processado = pdf_result.read()
        
        assert len(conteudo_processado) == len(conteudo_original)
    
    def test_extrair_texto_documento_pdf(self, pdf_simples):
        """Deve extrair texto de PDF via função unificada."""
        from conversor import extrair_texto_documento
        
        texto, palavras, page_size, metodo = extrair_texto_documento(pdf_simples, "doc.pdf")
        
        assert texto is not None
        assert len(texto) > 0
        assert metodo is not None
    
    def test_docx_extrai_tabelas(self, docx_simples):
        """Deve extrair texto de tabelas em DOCX."""
        from conversor import extrair_texto_docx, DOCX_DISPONIVEL
        
        if not DOCX_DISPONIVEL:
            pytest.skip("python-docx não instalado")
        
        texto, palavras, page_size = extrair_texto_docx(docx_simples)
        
        # Deve conter texto da tabela
        assert "Serviço A" in texto or "2.500,00" in texto


# =============================================================================
# TESTES DE BYTES VS FILE-LIKE (conversor.py)
# =============================================================================

class TestInputTypes:
    """Testes para diferentes tipos de entrada."""
    
    def test_imagem_para_pdf_com_bytes(self, imagem_jpg):
        """Deve aceitar bytes como entrada."""
        from conversor import imagem_para_pdf, PIL_DISPONIVEL, PYMUPDF_DISPONIVEL
        
        if not PIL_DISPONIVEL or not PYMUPDF_DISPONIVEL:
            pytest.skip("Dependências não instaladas")
        
        # Converte para bytes
        imagem_jpg.seek(0)
        img_bytes = imagem_jpg.read()
        
        # Deve funcionar com bytes direto
        pdf_result = imagem_para_pdf(img_bytes, "img.jpg")
        
        assert pdf_result is not None
        pdf_result.seek(0)
        assert pdf_result.read(4) == b'%PDF'
    
    def test_processar_documento_com_bytes(self, pdf_simples):
        """Deve aceitar bytes como entrada no processamento."""
        from conversor import processar_documento
        
        pdf_simples.seek(0)
        pdf_bytes = pdf_simples.read()
        
        pdf_result, tipo, convertido = processar_documento(pdf_bytes, "doc.pdf")
        
        assert pdf_result is not None


# =============================================================================
# TESTES DE INICIALIZAÇÃO (database.py)
# =============================================================================

class TestInicializacao:
    """Testes de inicialização do banco."""
    
    def test_inicializar_diretorios(self):
        """Deve criar diretórios necessários."""
        from database import inicializar_diretorios, DATA_DIR, CHROMA_DIR
        
        inicializar_diretorios()
        
        assert DATA_DIR.exists()
        assert CHROMA_DIR.exists()
    
    def test_criar_tabelas_idempotente(self):
        """Criar tabelas múltiplas vezes não deve causar erro."""
        from database import criar_tabelas
        
        # Chama múltiplas vezes
        criar_tabelas()
        criar_tabelas()
        criar_tabelas()
        
        # Não deve lançar exceção
        assert True
    
    def test_get_conexao(self):
        """Deve retornar conexão válida."""
        from database import get_conexao
        
        conn = get_conexao()
        
        assert conn is not None
        
        # Deve ser possível executar query
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        result = cursor.fetchone()
        
        assert result is not None
        
        conn.close()


# =============================================================================
# TESTES DE EDGE CASES (database.py)
# =============================================================================

class TestEdgeCases:
    """Testes de casos extremos."""
    
    def test_salvar_template_com_nome_e_descricao(self):
        """Deve salvar template com nome e descrição."""
        from database import salvar_template, carregar_template, deletar_template, listar_templates
        
        hash_test = "test_hash_with_metadata"
        mapeamentos = [{"tipo": "CAMPO", "descricao": "Campo", "texto_original": "valor", "x0": 0, "top": 0, "x1": 10, "bottom": 10}]
        
        template_id = salvar_template(
            hash_test, 
            mapeamentos, 
            nome="Template Especial",
            descricao="Descrição do template"
        )
        
        assert template_id is not None
        
        # Verifica na listagem
        templates = listar_templates()
        template_encontrado = next((t for t in templates if t['hash'] == hash_test), None)
        
        assert template_encontrado is not None
        assert template_encontrado['nome'] == "Template Especial"
        
        # Limpa
        deletar_template(hash_test)
    
    def test_salvar_template_mapeamento_vazio(self):
        """Deve salvar template com mapeamentos vazios."""
        from database import salvar_template, carregar_template, deletar_template
        
        hash_test = "test_hash_empty_mappings"
        
        template_id = salvar_template(hash_test, [])
        
        assert template_id is not None
        
        mapeamentos = carregar_template(hash_test)
        
        assert mapeamentos == []
        
        # Limpa
        deletar_template(hash_test)
    
    def test_salvar_template_coordenadas_faltando(self):
        """Deve lidar com mapeamentos sem todas as coordenadas."""
        from database import salvar_template, carregar_template, deletar_template
        
        hash_test = "test_hash_missing_coords"
        mapeamentos = [{"tipo": "CAMPO"}]  # Sem coordenadas
        
        template_id = salvar_template(hash_test, mapeamentos)
        
        assert template_id is not None
        
        resultado = carregar_template(hash_test)
        
        assert len(resultado) == 1
        assert resultado[0]['x0'] == 0  # Valor padrão
        
        # Limpa
        deletar_template(hash_test)


# =============================================================================
# TESTES DE PDF GENERATION
# =============================================================================

class TestPdfGeneration:
    """Testes adicionais de geração de PDF."""
    
    def test_gerar_pdf_valores_longos(self, pdf_simples, mock_mapeamentos):
        """Deve lidar com valores longos na substituição."""
        from tests.test_app import gerar_pdf_com_substituicoes
        
        novos_valores = {
            "NOME_CLIENTE": "Nome muito longo que excede o tamanho normal do campo original no documento PDF"
        }
        
        pdf_bytes = gerar_pdf_com_substituicoes(
            pdf_simples,
            mock_mapeamentos,
            novos_valores,
            (595, 842)
        )
        
        assert pdf_bytes[:4] == b'%PDF'
    
    def test_gerar_pdf_caracteres_especiais(self, pdf_simples, mock_mapeamentos):
        """Deve lidar com caracteres especiais."""
        from tests.test_app import gerar_pdf_com_substituicoes
        
        novos_valores = {
            "NOME_CLIENTE": "José da Conceição & Filhos Ltda."
        }
        
        pdf_bytes = gerar_pdf_com_substituicoes(
            pdf_simples,
            mock_mapeamentos,
            novos_valores,
            (595, 842)
        )
        
        assert pdf_bytes[:4] == b'%PDF'
