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
# CHROMADB - Busca por Similaridade
# =============================================================================

# Limiar de similaridade (0.0 a 1.0) - quanto maior, mais similar deve ser
LIMIAR_SIMILARIDADE = 0.75


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


def normalizar_texto_para_embedding(texto: str) -> str:
    """
    Normaliza o texto do documento para criar embedding.
    Remove valores variaveis e mantem apenas a estrutura.
    """
    import re

    # Remove numeros
    texto = re.sub(r'\d+', ' NUM ', texto)

    # Remove valores monetarios
    texto = re.sub(r'R\$\s*[\d.,]+', ' VALOR ', texto)

    # Remove datas
    texto = re.sub(r'\d{1,2}[/.-]\d{1,2}[/.-]\d{2,4}', ' DATA ', texto)

    # Remove CPF/CNPJ
    texto = re.sub(r'\d{3}[.\s]?\d{3}[.\s]?\d{3}[-.\s]?\d{2}', ' CPF ', texto)
    texto = re.sub(r'\d{2}[.\s]?\d{3}[.\s]?\d{3}[/.\s]?\d{4}[-.\s]?\d{2}', ' CNPJ ', texto)

    # Remove emails
    texto = re.sub(r'[\w.-]+@[\w.-]+\.\w+', ' EMAIL ', texto)

    # Remove telefones
    texto = re.sub(r'\(?\d{2}\)?\s*\d{4,5}[-.\s]?\d{4}', ' TELEFONE ', texto)

    # Remove multiplos espacos
    texto = re.sub(r'\s+', ' ', texto)

    return texto.strip().lower()


def salvar_embedding(doc_hash: str, texto_documento: str, template_id: int) -> bool:
    """
    Salva o embedding do documento no ChromaDB.

    Args:
        doc_hash: Hash unico do documento
        texto_documento: Texto completo do documento
        template_id: ID do template no SQLite

    Returns:
        True se salvou, False se ChromaDB nao disponivel
    """
    colecao = get_colecao_chroma()
    if colecao is None:
        return False

    try:
        # Normaliza o texto para embedding
        texto_normalizado = normalizar_texto_para_embedding(texto_documento)

        # Verifica se ja existe
        existentes = colecao.get(ids=[doc_hash])
        if existentes and existentes['ids']:
            # Atualiza
            colecao.update(
                ids=[doc_hash],
                documents=[texto_normalizado],
                metadatas=[{"template_id": template_id, "hash": doc_hash}]
            )
        else:
            # Insere novo
            colecao.add(
                ids=[doc_hash],
                documents=[texto_normalizado],
                metadatas=[{"template_id": template_id, "hash": doc_hash}]
            )

        return True

    except Exception as e:
        print(f"Erro ao salvar embedding: {e}")
        return False


def buscar_template_similar(texto_documento: str, limiar: float = None) -> Optional[Tuple[str, float, List[dict]]]:
    """
    Busca um template similar no ChromaDB.

    Args:
        texto_documento: Texto do documento a buscar
        limiar: Limiar minimo de similaridade (0.0 a 1.0)

    Returns:
        Tupla (hash, similaridade, mapeamentos) ou None se nao encontrou
    """
    colecao = get_colecao_chroma()
    if colecao is None:
        return None

    if limiar is None:
        limiar = LIMIAR_SIMILARIDADE

    try:
        # Normaliza o texto para busca
        texto_normalizado = normalizar_texto_para_embedding(texto_documento)

        # Busca os mais similares
        resultados = colecao.query(
            query_texts=[texto_normalizado],
            n_results=1,
            include=["distances", "metadatas"]
        )

        if not resultados or not resultados['ids'] or not resultados['ids'][0]:
            return None

        # ChromaDB retorna distancia (menor = mais similar)
        # Convertemos para similaridade (maior = mais similar)
        distancia = resultados['distances'][0][0]
        similaridade = 1.0 / (1.0 + distancia)  # Converte distancia em similaridade

        if similaridade < limiar:
            return None

        # Recupera o hash do template encontrado
        hash_encontrado = resultados['metadatas'][0][0]['hash']

        # Carrega os mapeamentos do SQLite
        mapeamentos = carregar_template(hash_encontrado)

        if mapeamentos is None:
            return None

        return (hash_encontrado, similaridade, mapeamentos)

    except Exception as e:
        print(f"Erro na busca por similaridade: {e}")
        return None


def deletar_embedding(doc_hash: str) -> bool:
    """
    Deleta um embedding do ChromaDB.

    Args:
        doc_hash: Hash do documento

    Returns:
        True se deletou, False se nao encontrou ou erro
    """
    colecao = get_colecao_chroma()
    if colecao is None:
        return False

    try:
        colecao.delete(ids=[doc_hash])
        return True
    except Exception:
        return False


def contar_embeddings() -> int:
    """Retorna o numero de embeddings no ChromaDB."""
    colecao = get_colecao_chroma()
    if colecao is None:
        return 0

    return colecao.count()


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

    print("\n[4] Testando operacoes SQLite...")

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

    # =============================================================================
    # TESTE DO CHROMADB
    # =============================================================================

    if CHROMADB_DISPONIVEL:
        print("\n[5] Testando ChromaDB (busca por similaridade)...")

        # Texto de exemplo (simula um documento)
        texto_doc1 = """
        NOTA FISCAL
        Cliente: Joao Silva
        CPF: 123.456.789-00
        Data: 15/12/2024
        Valor Total: R$ 1.500,00
        """

        # Salva embedding
        salvou = salvar_embedding("hash_teste_123", texto_doc1, template_id)
        print(f"    - Embedding salvo: {salvou}")

        # Conta embeddings
        total_embeddings = contar_embeddings()
        print(f"    - Total de embeddings: {total_embeddings}")

        # Texto similar (mesmo template, dados diferentes)
        texto_doc2 = """
        NOTA FISCAL
        Cliente: Maria Santos
        CPF: 987.654.321-00
        Data: 20/12/2024
        Valor Total: R$ 2.300,00
        """

        # Busca por similaridade
        resultado = buscar_template_similar(texto_doc2)
        if resultado:
            hash_enc, similaridade, maps = resultado
            print(f"    - Template similar encontrado!")
            print(f"      Hash: {hash_enc}")
            print(f"      Similaridade: {similaridade:.2%}")
            print(f"      Campos: {len(maps)}")
        else:
            print("    - Nenhum template similar encontrado")

        print(f"\n[6] Caminho do ChromaDB: {CHROMA_DIR}")

    print("\n" + "=" * 60)
    print("BANCO DE DADOS FUNCIONANDO!")
    print("=" * 60)
