# Testes - Reverse Templating POC

Este diretório contém a suíte de testes automatizados para o projeto.

## 📊 Resumo

- **119 testes** passando
- **74% de cobertura** nos módulos principais
- **~5 segundos** de execução

## Estrutura

```
tests/
├── __init__.py              # Pacote de testes
├── conftest.py              # Fixtures compartilhadas
├── test_app.py              # Testes das funções principais
├── test_conversor.py        # Testes do módulo de conversão
├── test_database.py         # Testes do banco de dados
├── test_ocr_engine.py       # Testes do motor de OCR
├── test_cobertura_extra.py  # Testes adicionais de cobertura
├── test_integracao.py       # Testes de integração
└── README.md                # Este arquivo
```

## Cobertura por Módulo

| Módulo | Linhas | Cobertura |
|--------|--------|-----------|
| conversor.py | 188 | 78% |
| ocr_engine.py | 172 | 76% |
| database.py | 215 | 70% |
| **TOTAL** | **575** | **74%** |

## Executando os Testes

### Todos os testes
```bash
python -m pytest tests/ -v
```

### Testes com cobertura
```bash
python -m pytest tests/ --cov=conversor --cov=database --cov=ocr_engine --cov-report=term-missing
```

### Testes rápidos (sem integração)
```bash
python -m pytest tests/ -v -m "not integration"
```

### Testes específicos
```bash
# Apenas testes do conversor
python -m pytest tests/test_conversor.py -v

# Apenas testes do database
python -m pytest tests/test_database.py -v

# Apenas testes do OCR
python -m pytest tests/test_ocr_engine.py -v

# Apenas testes de integração
python -m pytest tests/test_integracao.py -v
```

### Executar teste específico
```bash
python -m pytest tests/test_conversor.py::TestDeteccaoFormato::test_eh_pdf_valido -v
```

### Gerar relatório HTML de cobertura
```bash
python -m pytest tests/ --cov=. --cov-report=html
# Abre htmlcov/index.html no navegador
```

## Fixtures Disponíveis

As seguintes fixtures estão disponíveis em `conftest.py`:

| Fixture | Descrição |
|---------|-----------|
| `pdf_simples` | PDF com campos típicos (nome, CPF, data, valor) |
| `pdf_vazio` | PDF sem conteúdo de texto |
| `imagem_com_texto` | Imagem PNG com texto para testes de OCR |
| `imagem_jpg` | Imagem JPG simples |
| `imagem_bmp` | Imagem BMP simples |
| `docx_simples` | Documento Word com campos típicos |
| `mock_mapeamentos` | Mapeamentos de exemplo para testes |
| `mock_variaveis_llm` | Variáveis simuladas da LLM |
| `mock_palavras` | Lista de palavras com coordenadas |

## Arquivos de Teste

### test_conversor.py (30 testes)
- Detecção de formato (PDF, imagem, Word)
- Conversão de imagem para PDF
- Conversão de Word para PDF
- Extração de texto de diferentes formatos

### test_database.py (16 testes)
- CRUD de templates (criar, ler, atualizar, deletar)
- Busca por similaridade (ChromaDB)
- Integridade de dados

### test_ocr_engine.py (16 testes)
- Verificação do Tesseract
- Extração com pdfplumber
- Detecção de PDF escaneado
- Extração automática

### test_app.py (15 testes)
- Hash de documento
- Mapeamento de variáveis
- Geração de PDF com substituições

### test_cobertura_extra.py (27 testes)
- Normalização de texto para embedding
- Funções do ChromaDB
- Tipos de entrada (bytes, file-like)
- Edge cases

### test_integracao.py (15 testes)
- Fluxos completos
- Ciclo de vida de templates
- Testes de constantes

## Requisitos

Instale as dependências de teste:
```bash
pip install pytest pytest-cov pytest-mock
```

Ou instale todas as dependências do projeto:
```bash
pip install -r requirements.txt
```

## Markers Personalizados

Os seguintes markers estão disponíveis:

- `@pytest.mark.slow` - Testes lentos
- `@pytest.mark.integration` - Testes de integração
- `@pytest.mark.ocr` - Testes que dependem do Tesseract

Para pular testes que dependem do Tesseract:
```bash
python -m pytest tests/ -v -m "not ocr"
```

## Notas

- Alguns testes são automaticamente pulados se as dependências não estiverem instaladas (ex: Tesseract, python-docx)
- Os testes de database usam o banco real, mas limpam os dados de teste após execução
- A fixture `docx_simples` requer python-docx instalado
