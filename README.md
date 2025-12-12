# Reverse Templating - POC

Sistema de identificacao e substituicao de variaveis em documentos PDF utilizando Inteligencia Artificial.

## Sobre o Projeto

Este projeto implementa um sistema de "Reverse Templating" que:

1. **Extrai** texto e coordenadas de documentos PDF
2. **Identifica** automaticamente campos variaveis (Nome, Valor, Data) usando IA
3. **Mapeia** os campos identificados com suas posicoes no documento
4. **Gera** um novo PDF com os valores substituidos mantendo o layout original

## Tecnologias Utilizadas

- **Python 3.10+**
- **Streamlit** - Interface web
- **pdfplumber** - Extracao de texto e coordenadas de PDFs
- **Google Gemini** - Modelo de IA para identificacao de variaveis
- **ReportLab** - Geracao de PDFs
- **PyPDF2** - Manipulacao de PDFs
- **LangChain** - Orquestracao de LLM

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

### 4. Configure as variaveis de ambiente

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

## Estrutura do Projeto

```
reverse-templating/
├── app.py                  # Interface web (Streamlit)
├── main.py                 # Script de linha de comando
├── criar_pdf_exemplo.py    # Gerador de PDF de teste
├── requirements.txt        # Dependencias do projeto
├── .env.example           # Exemplo de configuracao
├── .gitignore             # Arquivos ignorados pelo Git
└── README.md              # Documentacao
```

## Fluxo de Funcionamento

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  Upload PDF     │────>│  Extracao OCR   │────>│  Analise IA     │
│                 │     │  (pdfplumber)   │     │  (Gemini)       │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                                                        │
                                                        v
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  Novo PDF       │<────│  Geracao PDF    │<────│  Mapeamento     │
│                 │     │  (ReportLab)    │     │  Coordenadas    │
└─────────────────┘     └─────────────────┘     └─────────────────┘
```

## Campos Identificados

O sistema identifica automaticamente:

- **NOME_CLIENTE** - Nomes de pessoas ou empresas
- **VALOR_TOTAL** - Valores monetarios (R$ X.XXX,XX)
- **DATA_DOCUMENTO** - Datas no formato brasileiro (DD/MM/AAAA)

## Licenca

Este projeto e uma Prova de Conceito (POC) desenvolvida para fins de estudo e demonstracao.

## Autor

PitangaTech
