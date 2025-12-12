# Reverse Templating - POC

Sistema de identificacao e substituicao de variaveis em documentos PDF utilizando Inteligencia Artificial.

## Sobre o Projeto

Este projeto implementa um sistema de "Reverse Templating" que:

1. **Extrai** texto e coordenadas de documentos PDF (texto nativo ou OCR)
2. **Identifica** automaticamente TODOS os campos variaveis usando IA (Google Gemini)
3. **Mapeia** os campos identificados com suas posicoes no documento
4. **Armazena** templates em banco de dados para reutilizacao
5. **Gera** um novo PDF com os valores substituidos mantendo o layout original

## Tecnologias Utilizadas

| Tecnologia | Funcao |
|------------|--------|
| Python 3.10+ | Linguagem principal |
| Streamlit | Interface web |
| pdfplumber | Extracao de texto nativo |
| Tesseract OCR | Extracao de PDFs escaneados |
| Google Gemini | Modelo de IA para identificacao |
| ReportLab | Geracao de PDFs |
| PyPDF2 | Manipulacao de PDFs |
| LangChain | Orquestracao de LLM |
| SQLite | Persistencia de templates |
| ChromaDB | Busca por similaridade (futuro) |

## Instalacao

### 1. Clone o repositorio

```bash
git clone https://github.com/seu-usuario/reverse-templating.git
cd reverse-templating
```

### 2. Crie um ambiente virtual (recomendado)

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

### 3. Instale as dependencias

```bash
pip install -r requirements.txt
```

### 4. Instale o Tesseract OCR (opcional, para PDFs escaneados)

**Windows:**
1. Baixe o instalador: https://github.com/UB-Mannheim/tesseract/wiki
2. Execute o instalador
3. Adicione ao PATH: `C:\Program Files\Tesseract-OCR`

**Linux (Ubuntu/Debian):**
```bash
sudo apt-get install tesseract-ocr tesseract-ocr-por
```

**Mac:**
```bash
brew install tesseract tesseract-lang
```

### 5. Configure as variaveis de ambiente

```bash
# Copie o arquivo de exemplo
cp .env.example .env

# Edite o arquivo .env e adicione sua API Key do Google Gemini
```

Para obter sua API Key do Google Gemini:
1. Acesse: https://aistudio.google.com/app/apikey
2. Crie uma nova API Key
3. Cole no arquivo `.env`

## Como Executar

### Interface Web (Recomendado)

```bash
python -m streamlit run app.py
```

Acesse: http://localhost:8501

### Linha de Comando

```bash
# Primeiro, gere um PDF de exemplo
python criar_pdf_exemplo.py

# Execute o processamento
python main.py
```

### Testar Modulos Individualmente

```bash
# Testar OCR
python ocr_engine.py

# Testar Banco de Dados
python database.py
```

## Estrutura do Projeto

```
reverse-templating/
├── app.py                  # Interface web (Streamlit)
├── main.py                 # Script de linha de comando
├── ocr_engine.py           # Motor de OCR (Tesseract)
├── database.py             # Persistencia (SQLite + ChromaDB)
├── criar_pdf_exemplo.py    # Gerador de PDF de teste
├── requirements.txt        # Dependencias do projeto
├── .env.example            # Exemplo de configuracao
├── .gitignore              # Arquivos ignorados pelo Git
└── README.md               # Documentacao
```

## Fluxo de Funcionamento

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Upload PDF    │────>│  Calcula Hash   │────>│  Busca no DB    │
│                 │     │  do documento   │     │                 │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                                                        │
                              ┌─────────────────────────┼─────────────────────────┐
                              │                         │                         │
                              v                         v                         v
                    ┌─────────────────┐       ┌─────────────────┐       ┌─────────────────┐
                    │  Template       │       │  Extracao       │       │  Analise IA     │
                    │  encontrado!    │       │  OCR/Nativo     │       │  (Gemini)       │
                    │  (instantaneo)  │       │                 │       │                 │
                    └─────────────────┘       └─────────────────┘       └─────────────────┘
                              │                         │                         │
                              │                         │                         v
                              │                         │               ┌─────────────────┐
                              │                         │               │  Salva no DB    │
                              │                         │               │  (cache)        │
                              │                         │               └─────────────────┘
                              │                         │                         │
                              v                         v                         v
                    ┌─────────────────────────────────────────────────────────────┐
                    │                    Mapeamento de Coordenadas                │
                    └─────────────────────────────────────────────────────────────┘
                                                        │
                                                        v
                    ┌─────────────────┐       ┌─────────────────┐       ┌─────────────────┐
                    │  Edicao de      │────>  │  Geracao PDF    │────>  │  Download       │
                    │  Valores        │       │  (ReportLab)    │       │  Novo PDF       │
                    └─────────────────┘       └─────────────────┘       └─────────────────┘
```

## Campos Identificados Automaticamente

O sistema identifica automaticamente qualquer campo variavel, incluindo:

- Nomes de pessoas ou empresas
- Datas (qualquer formato)
- Valores monetarios
- Numeros de documentos (CPF, CNPJ, RG, etc.)
- Enderecos
- Telefones e emails
- Numeros de pedido, fatura, contrato
- Quantidades e percentuais
- Qualquer outro dado especifico do documento

## Recursos

- **Deteccao automatica** de PDFs escaneados vs texto nativo
- **Cache inteligente** de templates para processamento instantaneo
- **Interface web** intuitiva e responsiva
- **Suporte multilinguagem** no OCR (portugues + ingles)

## Seguranca

- API Keys sao armazenadas em variaveis de ambiente (`.env`)
- Arquivos sensiveis estao no `.gitignore`
- Banco de dados local (dados nao saem da maquina)

## Licenca

Este projeto e uma Prova de Conceito (POC) desenvolvida para fins de estudo e demonstracao.

## Autor

PitangaTech
