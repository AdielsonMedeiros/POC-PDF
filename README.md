# 📄 Reverse Templating MVP

Sistema inteligente de identificação e substituição de variáveis em documentos usando IA.

![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)
![Streamlit](https://img.shields.io/badge/Streamlit-1.28+-red.svg)
![Tests](https://img.shields.io/badge/Tests-119%20passing-brightgreen.svg)
![Coverage](https://img.shields.io/badge/Coverage-74%25-yellow.svg)
![Status](https://img.shields.io/badge/Status-MVP-orange.svg)

## 🎯 O que é?

O **Reverse Templating** é um produto que automatiza a identificação e substituição de campos variáveis em documentos:

1. **Upload de documentos** - PDF, imagens (PNG, JPG, TIFF) ou Word (DOCX)
2. **Análise inteligente** - IA identifica automaticamente campos variáveis (nomes, datas, valores, CPFs, etc.)
3. **Substituição fácil** - Preencha novos valores e gere um novo documento
4. **Aprendizado** - O sistema memoriza templates para processamento instantâneo de documentos similares

## ✨ Funcionalidades

- 🔍 **Detecção automática de campos** usando Google Gemini AI
- 📝 **Suporte a múltiplos formatos**: PDF, PNG, JPG, JPEG, BMP, TIFF, DOCX, DOC
- 🔄 **OCR integrado** para PDFs escaneados (Tesseract)
- 💾 **Banco de templates** com SQLite + ChromaDB
- 🔎 **Busca por similaridade** para encontrar templates parecidos
- 📊 **Interface web moderna** com Streamlit
- ✅ **Suite de testes** com 119 testes e 74% de cobertura

## 🚀 Início Rápido

### 1. Clone o repositório

```bash
git clone https://github.com/seu-usuario/reverse-templating.git
cd reverse-templating
```

### 2. Crie um ambiente virtual

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

### 3. Instale as dependências

```bash
pip install -r requirements.txt
```

### 4. Configure as variáveis de ambiente

Crie um arquivo `.env` na raiz do projeto:

```env
GOOGLE_API_KEY=sua_chave_api_do_google_gemini
```

> ⚠️ **Importante**: Nunca compartilhe sua API key. O arquivo `.env` está no `.gitignore`.

### 5. (Opcional) Instale o Tesseract para OCR

**Windows:**
- Baixe de: https://github.com/UB-Mannheim/tesseract/wiki
- Adicione ao PATH

**Linux (Ubuntu/Debian):**
```bash
sudo apt-get install tesseract-ocr tesseract-ocr-por
```

**Mac:**
```bash
brew install tesseract tesseract-lang
```

### 6. Execute a aplicação

```bash
streamlit run app.py
```

Acesse: http://localhost:8501

## 📁 Estrutura do Projeto

```
reverse-templating/
├── app.py              # Aplicação principal (Streamlit)
├── conversor.py        # Conversão de formatos (imagem/Word → PDF)
├── database.py         # Persistência (SQLite + ChromaDB)
├── ocr_engine.py       # Motor de OCR (Tesseract)
├── requirements.txt    # Dependências Python
├── .env.example        # Exemplo de configuração
├── .gitignore          # Arquivos ignorados pelo Git
├── tests/              # Testes automatizados
│   ├── conftest.py     # Fixtures compartilhadas
│   ├── test_*.py       # Arquivos de teste
│   └── README.md       # Documentação dos testes
└── data/               # Banco de dados local (ignorado pelo Git)
```

## 🧪 Testes

O projeto possui uma suíte completa de testes automatizados:

```bash
# Executar todos os testes
python -m pytest tests/ -v

# Executar com cobertura
python -m pytest tests/ --cov=conversor --cov=database --cov=ocr_engine

# Executar testes específicos
python -m pytest tests/test_conversor.py -v
```

### Métricas de Testes

| Métrica | Valor |
|---------|-------|
| Total de testes | 119 |
| Testes passando | 119 ✅ |
| Cobertura | 74% |

## 📋 Formatos Suportados

| Formato | Extensões | Processamento |
|---------|-----------|---------------|
| PDF | `.pdf` | Nativo ou OCR |
| Imagens | `.png`, `.jpg`, `.jpeg`, `.bmp`, `.tiff`, `.tif` | OCR + conversão para PDF |
| Word | `.docx`, `.doc` | Extração de texto + conversão para PDF |

## 🔧 Tecnologias

- **Interface**: Streamlit
- **IA/LLM**: Google Gemini (via LangChain)
- **PDF**: pdfplumber, PyMuPDF, ReportLab, PyPDF2
- **OCR**: Tesseract (pytesseract)
- **Banco de Dados**: SQLite + ChromaDB
- **Documentos Word**: python-docx
- **Testes**: pytest, pytest-cov

## 📖 Como Funciona

### 1. Upload do Documento
O usuário faz upload de um documento. Se não for PDF, é convertido automaticamente.

### 2. Cálculo de Hash
Um hash único é calculado baseado na "estrutura" do documento (ignorando valores variáveis).

### 3. Busca de Template
- **Hash exato**: Se o documento já foi processado, usa o template salvo (instantâneo)
- **Similaridade**: Se há um template similar (>75%), reutiliza os mapeamentos
- **Análise IA**: Caso contrário, a IA analisa e identifica os campos

### 4. Identificação de Campos
A IA (Gemini) identifica todos os campos variáveis:
- Nomes, CPFs, CNPJs
- Datas, valores monetários
- Endereços, telefones, emails
- Números de documentos, etc.

### 5. Mapeamento de Coordenadas
Os campos identificados são mapeados para suas posições exatas no PDF.

### 6. Geração do Documento
O usuário preenche novos valores e um novo PDF é gerado com as substituições.

## 🗺️ Roadmap

### ✅ MVP (Atual)
- [x] Suporte a PDF, Imagens e Word
- [x] Identificação de campos com IA
- [x] Banco de templates
- [x] Busca por similaridade
- [x] Suite de testes

### 🔜 Próximas versões
- [ ] Suporte a múltiplas páginas
- [ ] Edição visual de campos
- [ ] API REST para integração
- [ ] Autenticação de usuários
- [ ] Deploy em cloud (AWS/GCP)
- [ ] Batch processing (múltiplos documentos)

## 🤝 Contribuindo

1. Faça um fork do projeto
2. Crie uma branch para sua feature (`git checkout -b feature/nova-feature`)
3. Commit suas mudanças (`git commit -m 'Adiciona nova feature'`)
4. Push para a branch (`git push origin feature/nova-feature`)
5. Abra um Pull Request

## 📝 Licença

Este projeto é um MVP (Minimum Viable Product) em desenvolvimento ativo.

## ⚙️ Configuração para Desenvolvimento

### Obtendo a API Key do Google Gemini

1. Acesse: https://makersuite.google.com/app/apikey
2. Crie uma nova API key
3. Adicione ao arquivo `.env`

### Variáveis de Ambiente

| Variável | Descrição | Obrigatória |
|----------|-----------|-------------|
| `GOOGLE_API_KEY` | Chave da API do Google Gemini | ✅ Sim |

## 🐛 Problemas Comuns

### "GOOGLE_API_KEY não configurada"
Certifique-se de criar o arquivo `.env` com sua chave API.

### "Tesseract não encontrado"
Instale o Tesseract seguindo as instruções acima para seu sistema operacional.

### OCR retornando texto vazio
Verifique se os pacotes de idioma do Tesseract estão instalados (`tesseract-ocr-por` para português).

---


