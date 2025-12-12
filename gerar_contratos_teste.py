"""
=============================================================================
GERADOR DE CONTRATOS DE EXEMPLO PARA TESTES
=============================================================================
Gera diversos tipos de contratos em PDF para testar o Reverse Templating.
Execute: python gerar_contratos_teste.py
"""

import os
from datetime import datetime, timedelta
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY

# Cria pasta para os contratos
OUTPUT_DIR = "contratos_teste"
os.makedirs(OUTPUT_DIR, exist_ok=True)


def criar_contrato_trabalho(filename, dados):
    """Cria um contrato de trabalho."""
    doc = SimpleDocTemplate(
        os.path.join(OUTPUT_DIR, filename),
        pagesize=A4,
        rightMargin=2*cm,
        leftMargin=2*cm,
        topMargin=2*cm,
        bottomMargin=2*cm
    )
    
    styles = getSampleStyleSheet()
    titulo = ParagraphStyle('Titulo', parent=styles['Heading1'], alignment=TA_CENTER, fontSize=16, spaceAfter=30)
    normal = ParagraphStyle('Normal', parent=styles['Normal'], alignment=TA_JUSTIFY, fontSize=11, leading=14)
    
    elementos = []
    
    elementos.append(Paragraph("CONTRATO DE TRABALHO", titulo))
    elementos.append(Spacer(1, 20))
    
    texto = f"""
    <b>CONTRATANTE:</b> {dados['empresa']}, pessoa jurídica de direito privado, 
    inscrita no CNPJ sob o nº {dados['cnpj']}, com sede em {dados['endereco_empresa']}, 
    neste ato representada por seu representante legal.
    <br/><br/>
    <b>CONTRATADO:</b> {dados['empregado']}, brasileiro(a), portador(a) do CPF nº {dados['cpf']}, 
    RG nº {dados['rg']}, residente e domiciliado(a) em {dados['endereco_empregado']}.
    <br/><br/>
    As partes acima identificadas têm, entre si, justo e acertado o presente Contrato de Trabalho, 
    que se regerá pelas cláusulas seguintes:
    <br/><br/>
    <b>CLÁUSULA 1ª - DO OBJETO</b><br/>
    O CONTRATADO é admitido para exercer a função de <b>{dados['cargo']}</b>, 
    desempenhando as atividades inerentes ao cargo.
    <br/><br/>
    <b>CLÁUSULA 2ª - DA REMUNERAÇÃO</b><br/>
    O CONTRATANTE pagará ao CONTRATADO o salário mensal de <b>{dados['salario']}</b>, 
    a ser pago até o 5º dia útil do mês subsequente ao trabalhado.
    <br/><br/>
    <b>CLÁUSULA 3ª - DA JORNADA DE TRABALHO</b><br/>
    A jornada de trabalho será de {dados['jornada']} semanais, de segunda a sexta-feira, 
    das {dados['horario_inicio']} às {dados['horario_fim']}, com intervalo de 1 hora para almoço.
    <br/><br/>
    <b>CLÁUSULA 4ª - DO PRAZO</b><br/>
    O presente contrato terá início em <b>{dados['data_inicio']}</b>, sendo por prazo indeterminado.
    <br/><br/>
    <b>CLÁUSULA 5ª - DO FORO</b><br/>
    Fica eleito o foro da comarca de {dados['cidade']} para dirimir quaisquer dúvidas oriundas deste contrato.
    <br/><br/>
    E, por estarem assim justos e contratados, firmam o presente instrumento em duas vias.
    <br/><br/>
    {dados['cidade']}, {dados['data_assinatura']}.
    """
    
    elementos.append(Paragraph(texto, normal))
    elementos.append(Spacer(1, 50))
    
    # Assinaturas
    assinaturas = f"""
    <br/><br/>
    _______________________________<br/>
    <b>{dados['empresa']}</b><br/>
    CONTRATANTE
    <br/><br/><br/>
    _______________________________<br/>
    <b>{dados['empregado']}</b><br/>
    CONTRATADO
    """
    elementos.append(Paragraph(assinaturas, ParagraphStyle('Assinatura', alignment=TA_CENTER, fontSize=10)))
    
    doc.build(elementos)
    print(f"✅ Criado: {filename}")


def criar_contrato_prestacao_servicos(filename, dados):
    """Cria um contrato de prestação de serviços."""
    doc = SimpleDocTemplate(
        os.path.join(OUTPUT_DIR, filename),
        pagesize=A4,
        rightMargin=2*cm,
        leftMargin=2*cm,
        topMargin=2*cm,
        bottomMargin=2*cm
    )
    
    styles = getSampleStyleSheet()
    titulo = ParagraphStyle('Titulo', parent=styles['Heading1'], alignment=TA_CENTER, fontSize=16, spaceAfter=30)
    normal = ParagraphStyle('Normal', parent=styles['Normal'], alignment=TA_JUSTIFY, fontSize=11, leading=14)
    
    elementos = []
    
    elementos.append(Paragraph("CONTRATO DE PRESTAÇÃO DE SERVIÇOS", titulo))
    elementos.append(Spacer(1, 20))
    
    texto = f"""
    <b>CONTRATANTE:</b> {dados['contratante']}, inscrito no CPF/CNPJ sob o nº {dados['cpf_cnpj_contratante']}, 
    com endereço em {dados['endereco_contratante']}.
    <br/><br/>
    <b>CONTRATADA:</b> {dados['contratada']}, inscrita no CNPJ sob o nº {dados['cnpj_contratada']}, 
    com sede em {dados['endereco_contratada']}.
    <br/><br/>
    <b>CLÁUSULA 1ª - DO OBJETO</b><br/>
    A CONTRATADA prestará os seguintes serviços: <b>{dados['servico']}</b>.
    <br/><br/>
    <b>CLÁUSULA 2ª - DO VALOR</b><br/>
    Pelos serviços prestados, a CONTRATANTE pagará à CONTRATADA o valor de <b>{dados['valor']}</b>, 
    a ser pago da seguinte forma: {dados['forma_pagamento']}.
    <br/><br/>
    <b>CLÁUSULA 3ª - DO PRAZO</b><br/>
    O presente contrato terá vigência de {dados['prazo']}, com início em <b>{dados['data_inicio']}</b> 
    e término previsto para <b>{dados['data_fim']}</b>.
    <br/><br/>
    <b>CLÁUSULA 4ª - DAS OBRIGAÇÕES</b><br/>
    A CONTRATADA se compromete a executar os serviços com qualidade e dentro dos prazos estabelecidos.
    <br/><br/>
    <b>CLÁUSULA 5ª - DO FORO</b><br/>
    Fica eleito o foro da cidade de {dados['cidade']} para dirimir eventuais controvérsias.
    <br/><br/>
    {dados['cidade']}, {dados['data_assinatura']}.
    """
    
    elementos.append(Paragraph(texto, normal))
    elementos.append(Spacer(1, 50))
    
    assinaturas = f"""
    <br/><br/>
    _______________________________<br/>
    <b>{dados['contratante']}</b><br/>
    CONTRATANTE
    <br/><br/><br/>
    _______________________________<br/>
    <b>{dados['contratada']}</b><br/>
    CONTRATADA
    """
    elementos.append(Paragraph(assinaturas, ParagraphStyle('Assinatura', alignment=TA_CENTER, fontSize=10)))
    
    doc.build(elementos)
    print(f"✅ Criado: {filename}")


def criar_procuracao(filename, dados):
    """Cria uma procuração."""
    doc = SimpleDocTemplate(
        os.path.join(OUTPUT_DIR, filename),
        pagesize=A4,
        rightMargin=2*cm,
        leftMargin=2*cm,
        topMargin=2*cm,
        bottomMargin=2*cm
    )
    
    styles = getSampleStyleSheet()
    titulo = ParagraphStyle('Titulo', parent=styles['Heading1'], alignment=TA_CENTER, fontSize=18, spaceAfter=30)
    normal = ParagraphStyle('Normal', parent=styles['Normal'], alignment=TA_JUSTIFY, fontSize=11, leading=14)
    
    elementos = []
    
    elementos.append(Paragraph("PROCURAÇÃO", titulo))
    elementos.append(Spacer(1, 30))
    
    texto = f"""
    <b>OUTORGANTE:</b> {dados['outorgante']}, {dados['nacionalidade']}, {dados['estado_civil']}, 
    {dados['profissao']}, portador(a) do RG nº {dados['rg']} e CPF nº {dados['cpf']}, 
    residente e domiciliado(a) em {dados['endereco']}.
    <br/><br/>
    <b>OUTORGADO:</b> {dados['outorgado']}, inscrito na OAB/{dados['oab_estado']} sob o nº {dados['oab_numero']}, 
    com escritório em {dados['endereco_advogado']}.
    <br/><br/>
    <b>PODERES:</b> {dados['poderes']}
    <br/><br/>
    <b>FINALIDADE:</b> {dados['finalidade']}
    <br/><br/>
    Esta procuração é válida até <b>{dados['validade']}</b>.
    <br/><br/><br/>
    {dados['cidade']}, {dados['data']}.
    <br/><br/><br/><br/>
    _______________________________<br/>
    <b>{dados['outorgante']}</b><br/>
    OUTORGANTE
    """
    
    elementos.append(Paragraph(texto, normal))
    
    doc.build(elementos)
    print(f"✅ Criado: {filename}")


def criar_contrato_honorarios(filename, dados):
    """Cria um contrato de honorários advocatícios."""
    doc = SimpleDocTemplate(
        os.path.join(OUTPUT_DIR, filename),
        pagesize=A4,
        rightMargin=2*cm,
        leftMargin=2*cm,
        topMargin=2*cm,
        bottomMargin=2*cm
    )
    
    styles = getSampleStyleSheet()
    titulo = ParagraphStyle('Titulo', parent=styles['Heading1'], alignment=TA_CENTER, fontSize=16, spaceAfter=30)
    normal = ParagraphStyle('Normal', parent=styles['Normal'], alignment=TA_JUSTIFY, fontSize=11, leading=14)
    
    elementos = []
    
    elementos.append(Paragraph("CONTRATO DE HONORÁRIOS ADVOCATÍCIOS", titulo))
    elementos.append(Spacer(1, 20))
    
    texto = f"""
    <b>CONTRATANTE:</b> {dados['cliente']}, portador do CPF nº {dados['cpf_cliente']}, 
    residente em {dados['endereco_cliente']}, telefone {dados['telefone']}, e-mail {dados['email']}.
    <br/><br/>
    <b>CONTRATADO:</b> {dados['advogado']}, advogado inscrito na OAB/{dados['oab_estado']} nº {dados['oab_numero']}, 
    com escritório em {dados['endereco_escritorio']}.
    <br/><br/>
    <b>CLÁUSULA 1ª - DO OBJETO</b><br/>
    O CONTRATADO é constituído para {dados['objeto']}.
    <br/><br/>
    <b>CLÁUSULA 2ª - DOS HONORÁRIOS</b><br/>
    O CONTRATANTE pagará ao CONTRATADO os seguintes honorários:<br/>
    - Valor inicial: <b>{dados['valor_inicial']}</b><br/>
    - Honorários de êxito: <b>{dados['honorarios_exito']}</b> sobre o valor obtido
    <br/><br/>
    <b>CLÁUSULA 3ª - DA FORMA DE PAGAMENTO</b><br/>
    {dados['forma_pagamento']}
    <br/><br/>
    <b>CLÁUSULA 4ª - DAS DESPESAS</b><br/>
    As despesas processuais (custas, perícias, etc.) serão de responsabilidade do CONTRATANTE.
    <br/><br/>
    {dados['cidade']}, {dados['data']}.
    """
    
    elementos.append(Paragraph(texto, normal))
    elementos.append(Spacer(1, 50))
    
    assinaturas = f"""
    _______________________________<br/>
    <b>{dados['cliente']}</b><br/>
    CONTRATANTE
    <br/><br/><br/>
    _______________________________<br/>
    <b>{dados['advogado']}</b><br/>
    OAB/{dados['oab_estado']} nº {dados['oab_numero']}
    """
    elementos.append(Paragraph(assinaturas, ParagraphStyle('Assinatura', alignment=TA_CENTER, fontSize=10)))
    
    doc.build(elementos)
    print(f"✅ Criado: {filename}")


# =============================================================================
# GERAR CONTRATOS DE EXEMPLO
# =============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("GERANDO CONTRATOS DE TESTE")
    print("=" * 60)
    print()
    
    # Contrato de Trabalho 1
    criar_contrato_trabalho("contrato_trabalho_restaurante.pdf", {
        "empresa": "Restaurante Sabor Caseiro Ltda",
        "cnpj": "12.345.678/0001-90",
        "endereco_empresa": "Rua das Flores, 123, Centro, São Paulo/SP",
        "empregado": "Maria Aparecida Silva",
        "cpf": "123.456.789-00",
        "rg": "12.345.678-9",
        "endereco_empregado": "Av. Brasil, 456, Apt 101, Jardins, São Paulo/SP",
        "cargo": "Cozinheira",
        "salario": "R$ 2.500,00",
        "jornada": "44 horas",
        "horario_inicio": "08:00",
        "horario_fim": "17:00",
        "data_inicio": "01/01/2025",
        "cidade": "São Paulo/SP",
        "data_assinatura": "20/12/2024"
    })
    
    # Contrato de Trabalho 2
    criar_contrato_trabalho("contrato_trabalho_loja.pdf", {
        "empresa": "Moda Fashion Comércio de Roupas Ltda",
        "cnpj": "98.765.432/0001-11",
        "endereco_empresa": "Shopping Center Norte, Loja 45, São Paulo/SP",
        "empregado": "João Carlos Santos",
        "cpf": "987.654.321-00",
        "rg": "98.765.432-1",
        "endereco_empregado": "Rua das Palmeiras, 789, Vila Nova, São Paulo/SP",
        "cargo": "Vendedor",
        "salario": "R$ 1.800,00 + comissão",
        "jornada": "44 horas",
        "horario_inicio": "10:00",
        "horario_fim": "19:00",
        "data_inicio": "15/01/2025",
        "cidade": "São Paulo/SP",
        "data_assinatura": "10/01/2025"
    })
    
    # Contrato de Trabalho 3
    criar_contrato_trabalho("contrato_trabalho_escritorio.pdf", {
        "empresa": "Tech Solutions Informática S.A.",
        "cnpj": "11.222.333/0001-44",
        "endereco_empresa": "Av. Paulista, 1000, 10º andar, São Paulo/SP",
        "empregado": "Ana Paula Oliveira",
        "cpf": "111.222.333-44",
        "rg": "11.222.333-4",
        "endereco_empregado": "Rua Augusta, 500, Consolação, São Paulo/SP",
        "cargo": "Analista de Sistemas",
        "salario": "R$ 8.500,00",
        "jornada": "40 horas",
        "horario_inicio": "09:00",
        "horario_fim": "18:00",
        "data_inicio": "01/02/2025",
        "cidade": "São Paulo/SP",
        "data_assinatura": "25/01/2025"
    })
    
    # Contrato de Prestação de Serviços 1
    criar_contrato_prestacao_servicos("contrato_servicos_marketing.pdf", {
        "contratante": "Empresa ABC Comércio Ltda",
        "cpf_cnpj_contratante": "55.666.777/0001-88",
        "endereco_contratante": "Rua do Comércio, 100, Centro, Rio de Janeiro/RJ",
        "contratada": "Agência Digital XYZ Ltda",
        "cnpj_contratada": "99.888.777/0001-66",
        "endereco_contratada": "Av. Rio Branco, 200, Centro, Rio de Janeiro/RJ",
        "servico": "Gestão de mídias sociais e marketing digital",
        "valor": "R$ 5.000,00 mensais",
        "forma_pagamento": "Pagamento mensal até o dia 10 de cada mês",
        "prazo": "12 meses",
        "data_inicio": "01/01/2025",
        "data_fim": "31/12/2025",
        "cidade": "Rio de Janeiro/RJ",
        "data_assinatura": "20/12/2024"
    })
    
    # Contrato de Prestação de Serviços 2
    criar_contrato_prestacao_servicos("contrato_servicos_contabilidade.pdf", {
        "contratante": "Indústria Metal Forte Ltda",
        "cpf_cnpj_contratante": "33.444.555/0001-22",
        "endereco_contratante": "Distrito Industrial, Lote 50, Guarulhos/SP",
        "contratada": "Contabilidade Segura S/S",
        "cnpj_contratada": "22.111.000/0001-33",
        "endereco_contratada": "Av. Tiradentes, 300, Centro, Guarulhos/SP",
        "servico": "Serviços contábeis, fiscais e departamento pessoal",
        "valor": "R$ 3.500,00 mensais",
        "forma_pagamento": "Boleto bancário com vencimento todo dia 15",
        "prazo": "24 meses",
        "data_inicio": "01/02/2025",
        "data_fim": "31/01/2027",
        "cidade": "Guarulhos/SP",
        "data_assinatura": "15/01/2025"
    })
    
    # Procuração 1
    criar_procuracao("procuracao_trabalhista.pdf", {
        "outorgante": "Pedro Henrique Souza",
        "nacionalidade": "brasileiro",
        "estado_civil": "casado",
        "profissao": "motorista",
        "rg": "44.555.666-7",
        "cpf": "444.555.666-77",
        "endereco": "Rua das Acácias, 789, Jardim Primavera, Campinas/SP",
        "outorgado": "Dr. Carlos Alberto Ferreira",
        "oab_estado": "SP",
        "oab_numero": "123.456",
        "endereco_advogado": "Rua XV de Novembro, 100, Centro, Campinas/SP",
        "poderes": "Amplos poderes para representar o outorgante em ação trabalhista, podendo propor ações, apresentar defesas, recorrer, transigir, desistir, receber e dar quitação.",
        "finalidade": "Reclamação trabalhista contra a empresa Transportes Rápido Ltda.",
        "validade": "31/12/2025",
        "cidade": "Campinas/SP",
        "data": "10/01/2025"
    })
    
    # Procuração 2
    criar_procuracao("procuracao_civil.pdf", {
        "outorgante": "Fernanda Costa Lima",
        "nacionalidade": "brasileira",
        "estado_civil": "solteira",
        "profissao": "empresária",
        "rg": "77.888.999-0",
        "cpf": "777.888.999-00",
        "endereco": "Av. Beira Mar, 1500, Apt 1201, Boa Viagem, Recife/PE",
        "outorgado": "Dra. Amanda Rodrigues Silva",
        "oab_estado": "PE",
        "oab_numero": "54.321",
        "endereco_advogado": "Rua do Sol, 50, Sala 302, Recife Antigo, Recife/PE",
        "poderes": "Poderes especiais para representar o outorgante em ação de cobrança, com poderes para transigir, acordar, receber valores e dar quitação.",
        "finalidade": "Ação de cobrança de valores devidos pela empresa Construtora Delta Ltda.",
        "validade": "30/06/2025",
        "cidade": "Recife/PE",
        "data": "05/01/2025"
    })
    
    # Contrato de Honorários 1
    criar_contrato_honorarios("contrato_honorarios_trabalhista.pdf", {
        "cliente": "Roberto Almeida Nunes",
        "cpf_cliente": "888.999.000-11",
        "endereco_cliente": "Rua das Orquídeas, 321, Jardim Europa, Belo Horizonte/MG",
        "telefone": "(31) 99999-8888",
        "email": "roberto.nunes@email.com",
        "advogado": "Dr. Marcelo Pereira Santos",
        "oab_estado": "MG",
        "oab_numero": "98.765",
        "endereco_escritorio": "Av. Afonso Pena, 1500, Sala 1001, Centro, Belo Horizonte/MG",
        "objeto": "patrocinar os interesses do cliente em reclamação trabalhista contra a empresa Mineradora Sul S.A.",
        "valor_inicial": "R$ 2.000,00",
        "honorarios_exito": "20%",
        "forma_pagamento": "Entrada de R$ 1.000,00 na assinatura e R$ 1.000,00 em 30 dias",
        "cidade": "Belo Horizonte/MG",
        "data": "08/01/2025"
    })
    
    # Contrato de Honorários 2
    criar_contrato_honorarios("contrato_honorarios_familia.pdf", {
        "cliente": "Juliana Martins Pereira",
        "cpf_cliente": "222.333.444-55",
        "endereco_cliente": "Rua dos Ipês, 456, Jardim Botânico, Curitiba/PR",
        "telefone": "(41) 98888-7777",
        "email": "juliana.pereira@email.com",
        "advogado": "Dra. Patrícia Gonçalves",
        "oab_estado": "PR",
        "oab_numero": "45.678",
        "endereco_escritorio": "Rua XV de Novembro, 800, Sala 505, Centro, Curitiba/PR",
        "objeto": "patrocinar os interesses da cliente em ação de divórcio consensual",
        "valor_inicial": "R$ 4.500,00",
        "honorarios_exito": "Não aplicável",
        "forma_pagamento": "3 parcelas iguais de R$ 1.500,00",
        "cidade": "Curitiba/PR",
        "data": "12/01/2025"
    })
    
    print()
    print("=" * 60)
    print(f"✅ TODOS OS CONTRATOS CRIADOS NA PASTA: {OUTPUT_DIR}/")
    print("=" * 60)
    print()
    print("Contratos gerados:")
    for f in os.listdir(OUTPUT_DIR):
        print(f"  📄 {f}")
