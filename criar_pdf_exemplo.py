"""
=============================================================================
Script para criar um PDF de exemplo para testar o Reverse Templating
=============================================================================

Execute este script para gerar o arquivo 'input.pdf' de teste.
"""

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.pdfgen import canvas
from reportlab.lib.colors import black, gray, lightgrey

def criar_fatura_exemplo():
    """Cria uma fatura simples de exemplo."""

    c = canvas.Canvas("input.pdf", pagesize=A4)
    width, height = A4

    # Cabeçalho da empresa
    c.setFont("Helvetica-Bold", 20)
    c.drawString(2*cm, height - 2*cm, "EMPRESA EXEMPLO LTDA")

    c.setFont("Helvetica", 10)
    c.drawString(2*cm, height - 2.6*cm, "CNPJ: 12.345.678/0001-99")
    c.drawString(2*cm, height - 3.1*cm, "Rua das Flores, 123 - Centro")
    c.drawString(2*cm, height - 3.6*cm, "São Paulo - SP | CEP: 01234-567")

    # Linha separadora
    c.setStrokeColor(gray)
    c.line(2*cm, height - 4*cm, width - 2*cm, height - 4*cm)

    # Título do documento
    c.setFont("Helvetica-Bold", 16)
    c.drawString(2*cm, height - 5*cm, "FATURA DE SERVIÇOS")

    c.setFont("Helvetica", 10)
    c.drawString(width - 6*cm, height - 5*cm, "Nº: 2024-00001")

    # Dados do cliente - ESTES SERÃO IDENTIFICADOS PELA LLM
    c.setFont("Helvetica-Bold", 11)
    c.drawString(2*cm, height - 6.5*cm, "DADOS DO CLIENTE:")

    c.setFont("Helvetica", 10)
    c.drawString(2*cm, height - 7.2*cm, "Nome:")
    c.drawString(4*cm, height - 7.2*cm, "João Silva")  # <-- VARIÁVEL: NOME_CLIENTE

    c.drawString(2*cm, height - 7.8*cm, "CPF: 123.456.789-00")
    c.drawString(2*cm, height - 8.4*cm, "E-mail: joao@email.com")

    # Data do documento - VARIÁVEL
    c.drawString(width - 6*cm, height - 7.2*cm, "Data:")
    c.drawString(width - 4.5*cm, height - 7.2*cm, "10/12/2024")  # <-- VARIÁVEL: DATA_DOCUMENTO

    # Linha separadora
    c.line(2*cm, height - 9*cm, width - 2*cm, height - 9*cm)

    # Tabela de serviços
    c.setFont("Helvetica-Bold", 10)
    c.drawString(2*cm, height - 9.8*cm, "DESCRIÇÃO DOS SERVIÇOS")

    # Cabeçalho da tabela
    c.setFillColor(lightgrey)
    c.rect(2*cm, height - 11*cm, width - 4*cm, 0.7*cm, fill=True, stroke=True)

    c.setFillColor(black)
    c.setFont("Helvetica-Bold", 9)
    c.drawString(2.2*cm, height - 10.7*cm, "Serviço")
    c.drawString(10*cm, height - 10.7*cm, "Qtd")
    c.drawString(12*cm, height - 10.7*cm, "Valor Unit.")
    c.drawString(15*cm, height - 10.7*cm, "Subtotal")

    # Linhas da tabela
    c.setFont("Helvetica", 9)

    c.rect(2*cm, height - 11.7*cm, width - 4*cm, 0.7*cm, fill=False, stroke=True)
    c.drawString(2.2*cm, height - 11.4*cm, "Consultoria em TI")
    c.drawString(10*cm, height - 11.4*cm, "10")
    c.drawString(12*cm, height - 11.4*cm, "R$ 150,00")
    c.drawString(15*cm, height - 11.4*cm, "R$ 1.500,00")

    c.rect(2*cm, height - 12.4*cm, width - 4*cm, 0.7*cm, fill=False, stroke=True)
    c.drawString(2.2*cm, height - 12.1*cm, "Suporte Técnico")
    c.drawString(10*cm, height - 12.1*cm, "5")
    c.drawString(12*cm, height - 12.1*cm, "R$ 100,00")
    c.drawString(15*cm, height - 12.1*cm, "R$ 500,00")

    # Total
    c.setFont("Helvetica-Bold", 12)
    c.drawString(12*cm, height - 13.5*cm, "VALOR TOTAL:")
    c.drawString(15*cm, height - 13.5*cm, "R$ 2.000,00")  # <-- VARIÁVEL: VALOR_TOTAL

    # Linha separadora
    c.line(2*cm, height - 14.5*cm, width - 2*cm, height - 14.5*cm)

    # Observações
    c.setFont("Helvetica-Bold", 10)
    c.drawString(2*cm, height - 15.5*cm, "OBSERVAÇÕES:")

    c.setFont("Helvetica", 9)
    c.drawString(2*cm, height - 16.2*cm, "1. Pagamento via PIX ou transferência bancária.")
    c.drawString(2*cm, height - 16.8*cm, "2. Em caso de dúvidas, entre em contato pelo e-mail: contato@empresa.com")
    c.drawString(2*cm, height - 17.4*cm, "3. Esta fatura tem validade de 30 dias.")

    # Rodapé
    c.setFont("Helvetica", 8)
    c.setFillColor(gray)
    c.drawString(2*cm, 2*cm, "Documento gerado automaticamente para fins de teste - POC Reverse Templating")
    c.drawCentredString(width/2, 1.5*cm, "Página 1 de 1")

    c.save()
    print("✅ Arquivo 'input.pdf' criado com sucesso!")
    print("\nCampos variáveis no documento:")
    print("  - NOME_CLIENTE: 'João Silva'")
    print("  - DATA_DOCUMENTO: '10/12/2024'")
    print("  - VALOR_TOTAL: 'R$ 2.000,00'")


if __name__ == "__main__":
    criar_fatura_exemplo()
