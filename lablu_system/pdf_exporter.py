"""
Exportador de PDF do LaBlu System.
mostrar_sku=True  → Exportar Loja  (SKU + Código + Cor + Preço/Esgotado)
mostrar_sku=False → Exportar Cliente (só filamentos em estoque, sem SKU)
"""

from pathlib import Path
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    Image, KeepTogether
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT
import io

PAGE_W, PAGE_H = A4
MARGIN    = 1.5 * cm
CONTENT_W = PAGE_W - 2 * MARGIN

PRETO       = colors.HexColor("#1a1a1a")
CINZA_BORDA = colors.HexColor("#bbbbbb")
CINZA_LINHA = colors.HexColor("#f5f5f5")
CINZA_HEAD  = colors.HexColor("#e8e8e8")
BRANCO      = colors.white
VERDE       = colors.HexColor("#4F9900")
AZUL_SKU    = colors.HexColor("#1a6ef0")
VERMELHO    = colors.HexColor("#e02d2d")

IMG_PX = 56   # tamanho máximo da imagem em pixels antes de inserir no PDF
IMG_Q  = 72   # qualidade JPEG (0-95)


def _compress_image(path: str) -> str | None:
    """
    Redimensiona e comprime a imagem para no máximo IMG_PX x IMG_PX.
    Retorna o caminho original se PIL não estiver disponível.
    Retorna None se a imagem não puder ser aberta.
    """
    try:
        from PIL import Image as PILImage
        img = PILImage.open(path).convert("RGB")
        img.thumbnail((IMG_PX, IMG_PX), PILImage.LANCZOS)
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=IMG_Q, optimize=True)
        buf.seek(0)
        return buf   # retorna buffer em memória
    except ImportError:
        # PIL não instalado — usa o arquivo original
        return path
    except Exception:
        return None


class PDFExporter:
    def __init__(self, db):
        self.db = db

    def export(self, output_path: str, mostrar_sku: bool = False):
        doc = SimpleDocTemplate(
            output_path,
            pagesize=A4,
            leftMargin=MARGIN,
            rightMargin=MARGIN,
            topMargin=1.5 * cm,
            bottomMargin=1.5 * cm,
            title="LaBlu System — Catálogo de Filamentos",
            author="LaBlu System",
            compress=1,   # compressão de streams do PDF
        )

        story = []
        cats_com_fil = []
        for cat in self.db.get_categorias():
            if mostrar_sku:
                fils = self.db.get_filamentos(categoria_id=cat["id"])
            else:
                fils = self.db.get_filamentos(categoria_id=cat["id"], apenas_em_estoque=True)
            if fils:
                cats_com_fil.append((cat, fils))

        if not cats_com_fil:
            return

        col_widths = self._col_widths(mostrar_sku)
        header_row = self._build_header_row(mostrar_sku)

        for cat, filamentos in cats_com_fil:
            banner    = self._build_banner(cat["nome"])
            data_rows = [self._build_row(fil, mostrar_sku) for fil in filamentos]

            # Banner + cabeçalho + primeiras 2 linhas nunca quebram
            primeiras = [header_row] + data_rows[:2]
            story.append(KeepTogether([
                banner,
                Spacer(1, 0.3 * cm),
                self._make_table(primeiras, col_widths, mostrar_sku),
            ]))

            # Resto sem cabeçalho repetido
            if len(data_rows) > 2:
                story.append(self._make_table(
                    data_rows[2:], col_widths, mostrar_sku, is_continuation=True
                ))

            story.append(Spacer(1, 0.8 * cm))

        doc.build(story)

    # ── Banner ────────────────────────────────────────────────────────────

    def _build_banner(self, nome):
        partes = nome.split()
        texto  = f"{partes[0]} <b>{' '.join(partes[1:])}</b>" if len(partes) >= 2 else f"<b>{nome}</b>"
        style  = ParagraphStyle("Banner", fontName="Helvetica", fontSize=20,
                                textColor=BRANCO, alignment=TA_CENTER, leading=26)
        tbl = Table([[Paragraph(texto, style)]], colWidths=[CONTENT_W])
        tbl.setStyle(TableStyle([
            ("BACKGROUND",    (0, 0), (-1, -1), VERDE),
            ("TOPPADDING",    (0, 0), (-1, -1), 16),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 16),
            ("LEFTPADDING",   (0, 0), (-1, -1), 0),
            ("RIGHTPADDING",  (0, 0), (-1, -1), 0),
        ]))
        return tbl

    # ── Colunas ───────────────────────────────────────────────────────────

    def _col_widths(self, mostrar_sku):
        if mostrar_sku:
            col_sku   = 2.2 * cm
            col_cod   = 2.2 * cm
            col_img   = 1.8 * cm
            col_preco = 3.2 * cm
            col_qtd   = 1.8 * cm
            col_nome  = CONTENT_W - col_sku - col_cod - col_img - col_preco - col_qtd
            return [col_sku, col_cod, col_img, col_nome, col_preco, col_qtd]
        else:
            col_cod   = 2.5 * cm
            col_img   = 1.8 * cm
            col_preco = 3.2 * cm
            col_nome  = CONTENT_W - col_cod - col_img - col_preco
            return [col_cod, col_img, col_nome, col_preco]

    # ── Cabeçalho ─────────────────────────────────────────────────────────

    def _build_header_row(self, mostrar_sku):
        def hdr(text, align=TA_CENTER):
            return Paragraph(text, ParagraphStyle(
                "H", fontName="Helvetica-Bold", fontSize=9,
                textColor=colors.HexColor("#555555"), alignment=align,
                leftIndent=6 if align == TA_LEFT else 0,
            ))
        if mostrar_sku:
            return [hdr("SKU"), hdr("CÓDIGO"), hdr(""), hdr("COR", TA_LEFT), hdr("PREÇO"), hdr("QTD")]
        else:
            return [hdr("CÓDIGO"), hdr(""), hdr("COR", TA_LEFT), hdr("PREÇO")]

    # ── Tabela ────────────────────────────────────────────────────────────

    def _make_table(self, rows, col_widths, mostrar_sku, is_continuation=False):
        img_col   = 1 if not mostrar_sku else 2
        preco_col = len(col_widths) - 1

        cmds = [
            ("VALIGN",        (0, 0),  (-1, -1),              "MIDDLE"),
            ("ALIGN",         (0, 0),  (0, -1),               "CENTER"),
            ("ALIGN",         (img_col, 0), (img_col, -1),    "CENTER"),
            ("ALIGN",         (preco_col, 0), (preco_col, -1),"CENTER"),
            ("TOPPADDING",    (0, 0),  (-1, -1),              8),
            ("BOTTOMPADDING", (0, 0),  (-1, -1),              8),
            ("LEFTPADDING",   (0, 0),  (-1, -1),              8),
            ("RIGHTPADDING",  (0, 0),  (-1, -1),              8),
            ("GRID",          (0, 0),  (-1, -1),              0.5, CINZA_BORDA),
        ]
        if not is_continuation:
            cmds += [
                ("BACKGROUND",    (0, 0), (-1, 0), CINZA_HEAD),
                ("TOPPADDING",    (0, 0), (-1, 0), 6),
                ("BOTTOMPADDING", (0, 0), (-1, 0), 6),
                ("ROWBACKGROUNDS",(0, 1), (-1, -1), [BRANCO, CINZA_LINHA]),
            ]
        else:
            cmds += [("ROWBACKGROUNDS", (0, 0), (-1, -1), [BRANCO, CINZA_LINHA])]

        return Table(rows, colWidths=col_widths, style=TableStyle(cmds))

    # ── Linha de dados ────────────────────────────────────────────────────

    def _build_row(self, fil, mostrar_sku):
        if mostrar_sku:
            return [self._sku_cell(fil), self._cod_cell(fil),
                    self._img_cell(fil), self._nome_cell(fil),
                    self._preco_cell(fil, mostrar_sku), self._qtd_cell(fil)]
        else:
            return [self._cod_cell(fil), self._img_cell(fil),
                    self._nome_cell(fil), self._preco_cell(fil, mostrar_sku)]

    # ── Células ───────────────────────────────────────────────────────────

    def _sku_cell(self, fil):
        sku = fil.get("sku", "").strip()
        return Paragraph(sku or "—", ParagraphStyle(
            "FSKU", fontName="Helvetica-Bold", fontSize=10,
            textColor=AZUL_SKU, alignment=TA_CENTER, leading=14))

    def _cod_cell(self, fil):
        cod = fil.get("marca", "").strip()
        return Paragraph(cod or "—", ParagraphStyle(
            "FCod", fontName="Helvetica-Bold", fontSize=12,
            textColor=PRETO, alignment=TA_CENTER, leading=16))

    def _img_cell(self, fil):
        img_path = fil.get("imagem_path", "")
        if img_path and Path(img_path).exists():
            try:
                src = _compress_image(img_path)
                if src is not None:
                    img = Image(src, width=1.4 * cm, height=1.4 * cm)
                    img.hAlign = "CENTER"
                    return img
            except Exception:
                pass
        return Paragraph("", ParagraphStyle("vazio", fontSize=10))

    def _nome_cell(self, fil):
        nome = fil.get("nome", "").strip()
        return Paragraph(nome, ParagraphStyle(
            "FNome", fontName="Helvetica", fontSize=13,
            textColor=PRETO, leading=16, leftIndent=6))

    def _qtd_cell(self, fil):
        qtd = fil.get("quantidade", "").strip()
        return Paragraph(qtd or "—", ParagraphStyle(
            "FQtd", fontName="Helvetica-Bold", fontSize=12,
            textColor=PRETO, alignment=TA_CENTER, leading=16))

    def _preco_cell(self, fil, mostrar_sku=False):
        em_estoque = bool(fil.get("em_estoque", 1))
        if mostrar_sku and not em_estoque:
            return Paragraph("Esgotado", ParagraphStyle(
                "FEsgotado", fontName="Helvetica-Bold", fontSize=11,
                textColor=VERMELHO, alignment=TA_CENTER, leading=16))
        preco = fil.get("peso_total", "").strip()
        if preco and not preco.upper().startswith("R$"):
            preco = f"R$ {preco}"
        return Paragraph(preco or "—", ParagraphStyle(
            "FPreco", fontName="Helvetica", fontSize=13,
            textColor=PRETO, alignment=TA_CENTER, leading=16))