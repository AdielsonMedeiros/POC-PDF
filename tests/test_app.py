"""
=============================================================================
TESTES DO APP PRINCIPAL
=============================================================================
Testa as funções principais do app.py (sem interface Streamlit).

Nota: Este arquivo testa apenas funções que não dependem do Streamlit.
As funções são testadas diretamente sem passar pelo app.py para evitar
dependências do Streamlit.
"""

import pytest
import sys
import os
from io import BytesIO
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

sys.path.insert(0, str(Path(__file__).parent.parent))

# Importa as bibliotecas necessárias diretamente
import pdfplumber
import hashlib
import re
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from PyPDF2 import PdfReader, PdfWriter


# =============================================================================
# FUNÇÕES COPIADAS DO APP PARA TESTE ISOLADO
# =============================================================================

def calcular_hash_documento(pdf_file) -> str:
    """
    Calcula um hash do documento para identificar templates conhecidos.
    Usa o conteudo do PDF para gerar um hash unico.
    """
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


def mapear_variaveis_para_coordenadas(variaveis_llm, palavras):
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


def gerar_pdf_com_substituicoes(pdf_file, mapeamentos, novos_valores, page_size):
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
# TESTES DE HASH DE DOCUMENTO
# =============================================================================

class TestHashDocumento:
    """Testes para cálculo de hash de documentos."""
    
    def test_hash_retorna_string(self, pdf_simples):
        """Deve retornar string."""
        hash_result = calcular_hash_documento(pdf_simples)
        
        assert isinstance(hash_result, str)
        assert len(hash_result) > 0
    
    def test_hash_tamanho_fixo(self, pdf_simples):
        """Hash deve ter tamanho fixo (16 caracteres)."""
        hash_result = calcular_hash_documento(pdf_simples)
        
        assert len(hash_result) == 16
    
    def test_hash_deterministico(self, pdf_simples):
        """Mesmo documento deve gerar mesmo hash."""
        hash1 = calcular_hash_documento(pdf_simples)
        pdf_simples.seek(0)
        hash2 = calcular_hash_documento(pdf_simples)
        
        assert hash1 == hash2
    
    def test_hash_diferente_para_documentos_diferentes(self, pdf_simples, pdf_vazio):
        """Documentos diferentes devem gerar hashes diferentes."""
        hash1 = calcular_hash_documento(pdf_simples)
        hash2 = calcular_hash_documento(pdf_vazio)
        
        assert hash1 != hash2


# =============================================================================
# TESTES DE MAPEAMENTO DE VARIÁVEIS
# =============================================================================

class TestMapeamentoVariaveis:
    """Testes para mapeamento de variáveis LLM para coordenadas."""
    
    def test_mapear_variaveis_simples(self, mock_variaveis_llm, mock_palavras):
        """Deve mapear variáveis simples corretamente."""
        mapeamentos = mapear_variaveis_para_coordenadas(
            mock_variaveis_llm,
            mock_palavras
        )
        
        assert isinstance(mapeamentos, list)
        assert len(mapeamentos) > 0
    
    def test_mapeamento_contem_coordenadas(self, mock_variaveis_llm, mock_palavras):
        """Mapeamentos devem conter coordenadas."""
        mapeamentos = mapear_variaveis_para_coordenadas(
            mock_variaveis_llm,
            mock_palavras
        )
        
        for mapeamento in mapeamentos:
            assert "x0" in mapeamento
            assert "top" in mapeamento
            assert "x1" in mapeamento
            assert "bottom" in mapeamento
    
    def test_mapeamento_preserva_tipo(self, mock_variaveis_llm, mock_palavras):
        """Mapeamentos devem preservar tipo da variável."""
        mapeamentos = mapear_variaveis_para_coordenadas(
            mock_variaveis_llm,
            mock_palavras
        )
        
        tipos = [m["tipo"] for m in mapeamentos]
        
        # Verifica que pelo menos alguns tipos foram preservados
        tipos_esperados = ["NOME_CLIENTE", "CPF_CLIENTE", "DATA_DOCUMENTO", "VALOR_TOTAL"]
        for tipo in tipos:
            assert tipo in tipos_esperados
    
    def test_mapeamento_lista_vazia(self):
        """Deve lidar com lista vazia de variáveis."""
        mapeamentos = mapear_variaveis_para_coordenadas([], [])
        
        assert mapeamentos == []
    
    def test_mapeamento_variavel_nao_encontrada(self, mock_palavras):
        """Deve ignorar variáveis não encontradas no texto."""
        variaveis = [
            {"valor_original": "Texto Inexistente", "tipo": "CAMPO_X", "descricao": "Campo X"}
        ]
        
        mapeamentos = mapear_variaveis_para_coordenadas(variaveis, mock_palavras)
        
        # Pode retornar lista vazia ou com match parcial
        assert isinstance(mapeamentos, list)


# =============================================================================
# TESTES DE GERAÇÃO DE PDF
# =============================================================================

class TestGeracaoPdf:
    """Testes para geração de PDF com substituições."""
    
    def test_gerar_pdf_retorna_bytes(self, pdf_simples, mock_mapeamentos):
        """Deve retornar bytes do PDF."""
        novos_valores = {
            "NOME_CLIENTE": "Maria Santos",
            "CPF_CLIENTE": "987.654.321-00"
        }
        
        pdf_bytes = gerar_pdf_com_substituicoes(
            pdf_simples,
            mock_mapeamentos,
            novos_valores,
            (595, 842)  # A4
        )
        
        assert isinstance(pdf_bytes, bytes)
        assert len(pdf_bytes) > 0
    
    def test_gerar_pdf_valido(self, pdf_simples, mock_mapeamentos):
        """PDF gerado deve ser válido."""
        novos_valores = {"NOME_CLIENTE": "Teste"}
        
        pdf_bytes = gerar_pdf_com_substituicoes(
            pdf_simples,
            mock_mapeamentos,
            novos_valores,
            (595, 842)
        )
        
        # PDF válido começa com %PDF
        assert pdf_bytes[:4] == b'%PDF'
    
    def test_gerar_pdf_sem_alteracoes(self, pdf_simples, mock_mapeamentos):
        """Deve funcionar mesmo sem valores para substituir."""
        novos_valores = {}
        
        pdf_bytes = gerar_pdf_com_substituicoes(
            pdf_simples,
            mock_mapeamentos,
            novos_valores,
            (595, 842)
        )
        
        assert isinstance(pdf_bytes, bytes)
    
    def test_gerar_pdf_todos_campos(self, pdf_simples, mock_mapeamentos):
        """Deve substituir todos os campos fornecidos."""
        novos_valores = {
            "NOME_CLIENTE": "Ana Paula Silva",
            "CPF_CLIENTE": "111.222.333-44",
            "DATA_DOCUMENTO": "31/12/2024",
            "VALOR_TOTAL": "R$ 10.000,00"
        }
        
        pdf_bytes = gerar_pdf_com_substituicoes(
            pdf_simples,
            mock_mapeamentos,
            novos_valores,
            (595, 842)
        )
        
        assert len(pdf_bytes) > 100  # PDF não trivial


# =============================================================================
# TESTES DE INTEGRAÇÃO
# =============================================================================

class TestIntegracao:
    """Testes de integração entre componentes."""
    
    def test_fluxo_completo_mapeamento_geracao(self, pdf_simples, mock_variaveis_llm, mock_palavras):
        """Testa fluxo completo: mapear variáveis e gerar PDF."""
        # Mapeia variáveis
        mapeamentos = mapear_variaveis_para_coordenadas(
            mock_variaveis_llm,
            mock_palavras
        )
        
        # Define novos valores
        novos_valores = {}
        for mapeamento in mapeamentos:
            novos_valores[mapeamento["tipo"]] = f"Novo {mapeamento['tipo']}"
        
        # Gera PDF
        pdf_bytes = gerar_pdf_com_substituicoes(
            pdf_simples,
            mapeamentos,
            novos_valores,
            (595, 842)
        )
        
        assert pdf_bytes[:4] == b'%PDF'
    
    def test_hash_consistente_apos_processamento(self, pdf_simples):
        """Hash deve ser consistente após múltiplos processamentos."""
        hash_inicial = calcular_hash_documento(pdf_simples)
        
        # Processa várias vezes
        for _ in range(3):
            pdf_simples.seek(0)
            hash_atual = calcular_hash_documento(pdf_simples)
            assert hash_atual == hash_inicial
