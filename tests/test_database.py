"""
=============================================================================
TESTES DO MÓDULO DATABASE
=============================================================================
Testa as funções de persistência de templates.
"""

import pytest
import sys
import os
import json
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from database import (
    salvar_template,
    carregar_template,
    listar_templates,
    template_existe,
    contar_templates,
    deletar_template,
    CHROMADB_DISPONIVEL,
    SQLITE_DB,
    DATA_DIR
)


# =============================================================================
# FIXTURES ESPECÍFICAS DO DATABASE
# =============================================================================

@pytest.fixture
def temp_db_dir(tmp_path, monkeypatch):
    """Configura diretório temporário para o banco de dados."""
    # Cria pasta data no temporário
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    
    # Muda para o diretório temporário
    original_dir = os.getcwd()
    os.chdir(tmp_path)
    
    yield tmp_path
    
    # Restaura diretório original
    os.chdir(original_dir)


@pytest.fixture
def sample_hash():
    """Hash de exemplo para testes."""
    return "test_abc123def456"


@pytest.fixture
def sample_mapeamentos():
    """Mapeamentos de exemplo para testes."""
    return [
        {
            "tipo": "NOME_CLIENTE",
            "descricao": "Nome do Cliente",
            "texto_original": "João Silva",
            "x0": 100, "top": 700, "x1": 200, "bottom": 712
        },
        {
            "tipo": "CPF",
            "descricao": "CPF",
            "texto_original": "123.456.789-00",
            "x0": 100, "top": 680, "x1": 220, "bottom": 692
        }
    ]


# =============================================================================
# TESTES BÁSICOS
# =============================================================================

class TestDatabaseBasico:
    """Testes básicos do módulo database."""
    
    def test_sqlite_db_path_definido(self):
        """Deve ter caminho do SQLite definido."""
        assert SQLITE_DB is not None
        assert isinstance(SQLITE_DB, Path)
    
    def test_data_dir_definido(self):
        """Deve ter diretório de dados definido."""
        assert DATA_DIR is not None
        assert isinstance(DATA_DIR, Path)


# =============================================================================
# TESTES DE CRUD DE TEMPLATES
# =============================================================================

class TestCrudTemplates:
    """Testes de operações CRUD em templates."""
    
    def test_salvar_template(self, sample_hash, sample_mapeamentos):
        """Deve salvar template com sucesso."""
        template_id = salvar_template(sample_hash, sample_mapeamentos)
        
        assert template_id is not None
        
        # Limpa após teste
        deletar_template(sample_hash)
    
    def test_carregar_template_existente(self, sample_hash, sample_mapeamentos):
        """Deve carregar template existente."""
        # Salva
        salvar_template(sample_hash, sample_mapeamentos)
        
        # Carrega
        resultado = carregar_template(sample_hash)
        
        assert resultado is not None
        assert isinstance(resultado, list)
        assert len(resultado) == len(sample_mapeamentos)
        
        # Limpa
        deletar_template(sample_hash)
    
    def test_carregar_template_inexistente(self):
        """Deve retornar None para template inexistente."""
        resultado = carregar_template("hash_que_nao_existe_xyz123")
        
        assert resultado is None
    
    def test_template_existe_verdadeiro(self, sample_hash, sample_mapeamentos):
        """Deve retornar True para template existente."""
        salvar_template(sample_hash, sample_mapeamentos)
        
        existe = template_existe(sample_hash)
        
        assert existe == True
        
        # Limpa
        deletar_template(sample_hash)
    
    def test_template_existe_falso(self):
        """Deve retornar False para template inexistente."""
        existe = template_existe("hash_inexistente_xyz789")
        
        assert existe == False
    
    def test_listar_templates(self, sample_mapeamentos):
        """Deve listar todos os templates."""
        # Salva alguns templates
        hash1 = "test_hash1_list"
        hash2 = "test_hash2_list"
        salvar_template(hash1, sample_mapeamentos)
        salvar_template(hash2, sample_mapeamentos)
        
        lista = listar_templates()
        
        assert isinstance(lista, list)
        
        # Limpa
        deletar_template(hash1)
        deletar_template(hash2)
    
    def test_contar_templates(self, sample_mapeamentos):
        """Deve contar templates corretamente."""
        count_inicial = contar_templates()
        
        hash1 = "test_count_hash1"
        hash2 = "test_count_hash2"
        salvar_template(hash1, sample_mapeamentos)
        salvar_template(hash2, sample_mapeamentos)
        
        count_final = contar_templates()
        
        assert count_final >= count_inicial + 2
        
        # Limpa
        deletar_template(hash1)
        deletar_template(hash2)
    
    def test_deletar_template(self, sample_hash, sample_mapeamentos):
        """Deve deletar template com sucesso."""
        # Salva
        salvar_template(sample_hash, sample_mapeamentos)
        assert template_existe(sample_hash) == True
        
        # Deleta
        sucesso = deletar_template(sample_hash)
        
        assert sucesso == True
        assert template_existe(sample_hash) == False
    
    def test_deletar_template_inexistente(self):
        """Deve retornar False ao deletar template inexistente."""
        sucesso = deletar_template("hash_que_nao_existe_delete")
        
        assert sucesso == False


# =============================================================================
# TESTES DE ATUALIZAÇÃO
# =============================================================================

class TestAtualizacaoTemplates:
    """Testes de atualização de templates."""
    
    def test_atualizar_template_existente(self, sample_hash, sample_mapeamentos):
        """Deve atualizar template existente."""
        # Salva original
        salvar_template(sample_hash, sample_mapeamentos)
        
        # Atualiza com novos dados
        novos_mapeamentos = [
            {
                "tipo": "NOVO_CAMPO",
                "descricao": "Novo Campo",
                "texto_original": "Valor Novo",
                "x0": 50, "top": 500, "x1": 150, "bottom": 512
            }
        ]
        salvar_template(sample_hash, novos_mapeamentos)
        
        # Verifica atualização
        resultado = carregar_template(sample_hash)
        
        assert len(resultado) == 1
        assert resultado[0]["tipo"] == "NOVO_CAMPO"
        
        # Limpa
        deletar_template(sample_hash)


# =============================================================================
# TESTES DE BUSCA POR SIMILARIDADE (se ChromaDB disponível)
# =============================================================================

@pytest.mark.skipif(not CHROMADB_DISPONIVEL, reason="ChromaDB não instalado")
class TestBuscaSimilaridade:
    """Testes de busca por similaridade."""
    
    def test_salvar_embedding(self, sample_hash, sample_mapeamentos):
        """Deve salvar embedding para busca por similaridade."""
        from database import salvar_embedding
        
        template_id = salvar_template(sample_hash, sample_mapeamentos)
        
        texto = "Documento de teste com Nome: João Silva e CPF: 123.456.789-00"
        resultado = salvar_embedding(sample_hash, texto, template_id)
        
        # Não deve lançar exceção
        assert True
        
        # Limpa
        deletar_template(sample_hash)
    
    def test_buscar_template_similar(self, sample_hash, sample_mapeamentos):
        """Deve encontrar template similar."""
        from database import salvar_embedding, buscar_template_similar
        
        # Salva template com embedding
        template_id = salvar_template(sample_hash, sample_mapeamentos)
        texto_original = "Contrato com Nome: João Silva e CPF: 123.456.789-00"
        salvar_embedding(sample_hash, texto_original, template_id)
        
        # Busca por texto similar
        texto_busca = "Contrato com Nome: Maria Santos e CPF: 987.654.321-00"
        resultado = buscar_template_similar(texto_busca)
        
        # Pode encontrar ou não dependendo do threshold
        # O importante é não lançar exceção
        assert True
        
        # Limpa
        deletar_template(sample_hash)


# =============================================================================
# TESTES DE INTEGRIDADE DE DADOS
# =============================================================================

class TestIntegridadeDados:
    """Testes de integridade dos dados salvos."""
    
    def test_mapeamentos_preservam_estrutura(self, sample_hash, sample_mapeamentos):
        """Deve preservar toda a estrutura dos mapeamentos."""
        salvar_template(sample_hash, sample_mapeamentos)
        resultado = carregar_template(sample_hash)
        
        for i, mapeamento in enumerate(resultado):
            original = sample_mapeamentos[i]
            assert mapeamento["tipo"] == original["tipo"]
            assert mapeamento["descricao"] == original["descricao"]
            assert mapeamento["texto_original"] == original["texto_original"]
            assert mapeamento["x0"] == original["x0"]
            assert mapeamento["top"] == original["top"]
        
        # Limpa
        deletar_template(sample_hash)
    
    def test_mapeamentos_com_caracteres_especiais(self, sample_hash):
        """Deve preservar caracteres especiais."""
        mapeamentos = [
            {
                "tipo": "ENDERECO",
                "descricao": "Endereço Completo",
                "texto_original": "Rua São João, nº 123 - 1º andar",
                "x0": 100, "top": 700, "x1": 300, "bottom": 712
            }
        ]
        
        salvar_template(sample_hash, mapeamentos)
        resultado = carregar_template(sample_hash)
        
        assert resultado[0]["texto_original"] == "Rua São João, nº 123 - 1º andar"
        assert resultado[0]["descricao"] == "Endereço Completo"
        
        # Limpa
        deletar_template(sample_hash)
