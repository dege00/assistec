"""Geração das planilhas Excel (.xlsx) exportadas pelo administrador da loja."""
from django.http import HttpResponse
from django.utils import timezone
from openpyxl import Workbook
from openpyxl.cell import WriteOnlyCell
from openpyxl.styles import Font
from openpyxl.utils import get_column_letter

from .models import Cliente, Peca

FORMATO_MOEDA = '"R$" #,##0.00'
PREFIXOS_PERIGOSOS = ("=", "+", "-", "@", "\t", "\r", "\n")


def texto_seguro(valor):
    """Grava texto literal, evitando injeção de fórmula ao abrir no Excel.

    O Excel interpreta células iniciadas por = + - @ (ou tab/quebra de linha) como
    fórmula/comando; o apóstrofo força o conteúdo a ser tratado como texto.
    """
    if valor is None:
        return ""
    texto = str(valor)
    if texto[:1] in PREFIXOS_PERIGOSOS:
        return "'" + texto
    return texto


def _celula(ws, valor, negrito=False, formato=None):
    celula = WriteOnlyCell(ws, value=valor)
    if negrito:
        celula.font = Font(bold=True)
    if formato:
        celula.number_format = formato
    return celula


def gerar_planilha(cabecalhos, linhas, larguras, moedas=()):
    """Monta o .xlsx em memória (modo write_only). `linhas` é um iterável de listas."""
    wb = Workbook(write_only=True)
    ws = wb.create_sheet("Dados")
    ws.freeze_panes = "A2"  # congela a linha de cabeçalho
    for i, largura in enumerate(larguras, start=1):
        ws.column_dimensions[get_column_letter(i)].width = largura
    ws.append([_celula(ws, h, negrito=True) for h in cabecalhos])
    for linha in linhas:
        ws.append([
            _celula(ws, valor, formato=FORMATO_MOEDA if i in moedas else None)
            for i, valor in enumerate(linha, start=1)
        ])
    return wb


def resposta_xlsx(wb, nome):
    resposta = HttpResponse(
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    resposta["Content-Disposition"] = f'attachment; filename="{nome}"'
    wb.save(resposta)
    return resposta


def exportar_clientes(loja):
    cabecalhos = ["Nome", "Telefone", "E-mail", "CPF/CNPJ", "Observações", "Cadastrado em"]
    larguras = [30, 18, 30, 20, 45, 20]
    linhas = (
        [texto_seguro(c.nome), texto_seguro(c.telefone), texto_seguro(c.email),
         texto_seguro(c.documento), texto_seguro(c.observacoes),
         timezone.localtime(c.criado_em).strftime("%d/%m/%Y %H:%M")]
        for c in Cliente.objects.filter(loja=loja).order_by("nome").iterator()
    )
    return gerar_planilha(cabecalhos, linhas, larguras)


def exportar_pecas(loja):
    cabecalhos = ["Nome", "Código", "Custo", "Preço de venda", "Quantidade", "Estoque mínimo"]
    larguras = [30, 18, 14, 16, 12, 16]
    linhas = (
        [texto_seguro(p.nome), texto_seguro(p.sku), p.custo, p.preco, p.quantidade, p.minimo]
        for p in Peca.objects.filter(loja=loja).order_by("nome").iterator()
    )
    return gerar_planilha(cabecalhos, linhas, larguras, moedas={3, 4})
