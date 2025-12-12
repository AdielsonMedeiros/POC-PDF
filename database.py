"""
=============================================================================
DATABASE - Banco de Templates com SQLite + ChromaDB
=============================================================================

Este modulo gerencia a persistencia dos templates de documentos:
- SQLite: Armazena metadados e mapeamentos de coordenadas
- ChromaDB: Armazena embeddings para busca por similaridade (futuro)

Estrutura do banco:
- templates: Informacoes do template (hash, nome, data)
- mapeamentos: Coordenadas das variaveis de cada template
"""

import os
import json
import sqlite3
import hashlib
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from pathlib import Path

# Tenta importar ChromaDB (opcional para busca por similaridade)
try:
    import chromadb
    from chromadb.config import Settings
    CHROMADB_DISPONIVEL = True
except ImportError:
    CHROMADB_DISPONIVEL = False

# =============================================================================
# CONFIGURACAO
# =============================================================================

# Pasta para armazenar os bancos de dados
DATA_DIR = Path(__file__).parent / "data"
SQLITE_DB = DATA_DIR / "templates.db"
CHROMA_DIR = DATA_DIR / "chroma"


def inicializar_diretorios():
    """Cria os diretorios necessarios."""
    DATA_DIR.mkdir(exist_ok=True)
    CHROMA_DIR.mkdir(exist_ok=True)


# =============================================================================
# SQLITE - Metadados e Mapeamentos
# =============================================================================

def get_conexao() -> sqlite3.Connection:
    """Retorna uma conexao com o banco SQLite."""
    inicializar_diretorios()
    conn = sqlite3.connect(str(SQLITE_DB))
    conn.row_factory = sqlite3.Row
    return conn


def criar_tabelas():
    """Cria as tabelas do banco de dados."""
    conn = get_conexao()
    cursor = conn.cursor()

    # Tabela de templates
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS templates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            hash TEXT UNIQUE NOT NULL,
            nome TEXT,
            descricao TEXT,
            num_campos INTEGER DEFAULT 0,
            criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            atualizado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Tabela de mapeamentos (coordenadas das variaveis)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS mapeamentos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            template_id INTEGER NOT NULL,
            tipo TEXT NOT NULL,
            descricao TEXT,
            texto_original TEXT,
            x0 REAL,
            top REAL,
            x1 REAL,
            bottom REAL,
            FOREIGN KEY (template_id) REFERENCES templates(id) ON DELETE CASCADE
        )
    """)

    # Indice para busca rapida por hash
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_templates_hash ON templates(hash)
    """)

    conn.commit()
    conn.close()


def salvar_template(
    doc_hash: str,
    mapeamentos: List[dict],
    nome: str = None,
    descricao: str = None
) -> int:
    """
    Salva um template no banco de dados.

    Args:
        doc_hash: Hash unico do documento
        mapeamentos: Lista de dicts com as variaveis e coordenadas
        nome: Nome opcional para o template
        descricao: Descricao opcional

    Returns:
        ID do template salvo
    """
    criar_tabelas()
    conn = get_conexao()
    cursor = conn.cursor()

    try:
        # Verifica se ja existe
        cursor.execute("SELECT id FROM templates WHERE hash = ?", (doc_hash,))
        resultado = cursor.fetchone()

        if resultado:
            # Atualiza template existente
            template_id = resultado['id']

            cursor.execute("""
                UPDATE templates
                SET nome = COALESCE(?, nome),
                    descricao = COALESCE(?, descricao),
                    num_campos = ?,
                    atualizado_em = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (nome, descricao, len(mapeamentos), template_id))

            # Remove mapeamentos antigos
            cursor.execute("DELETE FROM mapeamentos WHERE template_id = ?", (template_id,))

        else:
            # Insere novo template
            cursor.execute("""
                INSERT INTO templates (hash, nome, descricao, num_campos)
                VALUES (?, ?, ?, ?)
            """, (doc_hash, nome, descricao, len(mapeamentos)))

            template_id = cursor.lastrowid

        # Insere mapeamentos
        for mapeamento in mapeamentos:
            cursor.execute("""
                INSERT INTO mapeamentos (template_id, tipo, descricao, texto_original, x0, top, x1, bottom)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                template_id,
                mapeamento.get('tipo', ''),
                mapeamento.get('descricao', ''),
                mapeamento.get('texto_original', ''),
                mapeamento.get('x0', 0),
                mapeamento.get('top', 0),
                mapeamento.get('x1', 0),
                mapeamento.get('bottom', 0)
            ))

        conn.commit()
        return template_id

    except Exception as e:
        conn.rollback()
        raise e

    finally:
        conn.close()


def carregar_template(doc_hash: str) -> Optional[List[dict]]:
    """
    Carrega um template do banco de dados pelo hash.

    Args:
        doc_hash: Hash do documento

    Returns:
        Lista de mapeamentos ou None se nao encontrado
    """
    criar_tabelas()
    conn = get_conexao()
    cursor = conn.cursor()

    try:
        # Busca o template
        cursor.execute("SELECT id FROM templates WHERE hash = ?", (doc_hash,))
        resultado = cursor.fetchone()

        if not resultado:
            return None

        template_id = resultado['id']

        # Busca os mapeamentos
        cursor.execute("""
            SELECT tipo, descricao, texto_original, x0, top, x1, bottom
            FROM mapeamentos
            WHERE template_id = ?
        """, (template_id,))

        mapeamentos = []
        for row in cursor.fetchall():
            mapeamentos.append({
                'tipo': row['tipo'],
                'descricao': row['descricao'],
                'texto_original': row['texto_original'],
                'x0': row['x0'],
                'top': row['top'],
                'x1': row['x1'],
                'bottom': row['bottom']
            })

        return mapeamentos

    finally:
        conn.close()


def listar_templates() -> List[dict]:
    """
    Lista todos os templates salvos.

    Returns:
        Lista de dicts com informacoes dos templates
    """
    criar_tabelas()
    conn = get_conexao()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT id, hash, nome, descricao, num_campos, criado_em, atualizado_em
            FROM templates
            ORDER BY atualizado_em DESC
        """)

        templates = []
        for row in cursor.fetchall():
            templates.append({
                'id': row['id'],
                'hash': row['hash'],
                'nome': row['nome'],
                'descricao': row['descricao'],
                'num_campos': row['num_campos'],
                'criado_em': row['criado_em'],
                'atualizado_em': row['atualizado_em']
            })

        return templates

    finally:
        conn.close()


def deletar_template(doc_hash: str) -> bool:
    """
    Deleta um template do banco.

    Args:
        doc_hash: Hash do documento

    Returns:
        True se deletou, False se nao encontrou
    """
    conn = get_conexao()
    cursor = conn.cursor()

    try:
        cursor.execute("DELETE FROM templates WHERE hash = ?", (doc_hash,))
        conn.commit()
        return cursor.rowcount > 0

    finally:
        conn.close()


def template_existe(doc_hash: str) -> bool:
    """Verifica se um template existe no banco."""
    criar_tabelas()
    conn = get_conexao()
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT 1 FROM templates WHERE hash = ?", (doc_hash,))
        return cursor.fetchone() is not None

    finally:
        conn.close()


def contar_templates() -> int:
    """Retorna o numero total de templates salvos."""
    criar_tabelas()
    conn = get_conexao()
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT COUNT(*) as total FROM templates")
        return cursor.fetchone()['total']

    finally:
        conn.close()


# =============================================================================
# CHROMADB - Busca por Similaridade (Futuro)
# =============================================================================

def get_colecao_chroma():
    """Retorna a colecao do ChromaDB para embeddings."""
    if not CHROMADB_DISPONIVEL:
        return None

    inicializar_diretorios()

    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    colecao = client.get_or_create_collection(
        name="templates",
        metadata={"description": "Embeddings dos templates de documentos"}
    )

    return colecao


# =============================================================================
# TESTE DO MODULO
# =============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("TESTE DO BANCO DE DADOS")
    print("=" * 60)

    print("\n[1] Verificando dependencias...")
    print(f"    - SQLite: OK (nativo do Python)")
    print(f"    - ChromaDB: {'OK' if CHROMADB_DISPONIVEL else 'NAO INSTALADO'}")

    print("\n[2] Criando tabelas...")
    criar_tabelas()
    print("    - Tabelas criadas com sucesso")

    print(f"\n[3] Caminho do banco: {SQLITE_DB}")

    print("\n[4] Testando operacoes...")

    # Teste de salvamento
    mapeamentos_teste = [
        {"tipo": "NOME_TESTE", "descricao": "Nome de Teste", "texto_original": "Joao", "x0": 10, "top": 20, "x1": 50, "bottom": 30},
        {"tipo": "DATA_TESTE", "descricao": "Data de Teste", "texto_original": "01/01/2025", "x0": 100, "top": 20, "x1": 150, "bottom": 30}
    ]

    template_id = salvar_template("hash_teste_123", mapeamentos_teste, nome="Template de Teste")
    print(f"    - Template salvo com ID: {template_id}")

    # Teste de carregamento
    mapeamentos_carregados = carregar_template("hash_teste_123")
    print(f"    - Template carregado: {len(mapeamentos_carregados)} campos")

    # Teste de listagem
    templates = listar_templates()
    print(f"    - Total de templates: {len(templates)}")

    # Teste de existencia
    existe = template_existe("hash_teste_123")
    print(f"    - Template existe: {existe}")

    print("\n" + "=" * 60)
    print("BANCO DE DADOS FUNCIONANDO!")
    print("=" * 60)
