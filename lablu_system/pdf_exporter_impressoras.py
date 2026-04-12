"""
Exportador de PDF de Impressoras do LaBlu System.
mostrar_sku=True  → Exportar Loja  (SKU + Código + Modelo + Preço + QTD)
mostrar_sku=False → Exportar Cliente (só em estoque, sem SKU e sem QTD)
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

IMG_PX = 56
IMG_Q  = 72


def _compress_image(path):
    try:
        from PIL import Image as PILImage
        img = PILImage.open(path).convert("RGB")
        img.thumbnail((IMG_PX, IMG_PX), PILImage.LANCZOS)
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=IMG_Q, optimize=True)
        buf.seek(0)
        return buf
    except ImportError:
        return path
    except Exception:
        return None


class PDFExporterImpressoras:
    def __init__(self, db):
        self.db = db

    def export(self, output_path: str, mostrar_sku: bool = False):
        doc = SimpleDocTemplate(
            output_path,
            pagesize=A4,
            leftMargin=MARGIN, rightMargin=MARGIN,
            topMargin=1.5 * cm, bottomMargin=1.5 * cm,
            title="LaBlu System — Catálogo de Impressoras",
            author="LaBlu System",
            compress=1,
        )

        story = []
        cats_com_imp = []
        for cat in self.db.get_categorias_impressoras():
            if mostrar_sku:
                imps = self.db.get_impressoras(categoria_id=cat["id"])
            else:
                imps = self.db.get_impressoras(categoria_id=cat["id"], apenas_em_estoque=True)
            if imps:
                cats_com_imp.append((cat, imps))

        if not cats_com_imp:
            return

        col_widths = self._col_widths(mostrar_sku)
        header_row = self._build_header_row(mostrar_sku)

        for cat, impressoras in cats_com_imp:
            banner    = self._build_banner(cat["nome"])
            data_rows = [self._build_row(imp, mostrar_sku) for imp in impressoras]

            primeiras = [header_row] + data_rows[:2]
            story.append(KeepTogether([
                banner,
                Spacer(1, 0.3 * cm),
                self._make_table(primeiras, col_widths, mostrar_sku),
            ]))

            if len(data_rows) > 2:
                story.append(self._make_table(
                    data_rows[2:], col_widths, mostrar_sku, is_continuation=True
                ))

            story.append(Spacer(1, 0.8 * cm))

        doc.build(story)

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

    def _col_widths(self, mostrar_sku):
        if mostrar_sku:
            col_sku    = 2.2 * cm
            col_cod    = 2.2 * cm
            col_img    = 1.8 * cm
            col_preco  = 3.0 * cm
            col_qtd    = 1.8 * cm
            col_modelo = CONTENT_W - col_sku - col_cod - col_img - col_preco - col_qtd
            return [col_sku, col_cod, col_img, col_modelo, col_preco, col_qtd]
        else:
            col_cod    = 2.5 * cm
            col_img    = 1.8 * cm
            col_preco  = 3.2 * cm
            col_modelo = CONTENT_W - col_cod - col_img - col_preco
            return [col_cod, col_img, col_modelo, col_preco]

    def _build_header_row(self, mostrar_sku):
        def hdr(text, align=TA_CENTER):
            return Paragraph(text, ParagraphStyle(
                "H", fontName="Helvetica-Bold", fontSize=9,
                textColor=colors.HexColor("#555555"), alignment=align,
                leftIndent=6 if align == TA_LEFT else 0,
            ))
        if mostrar_sku:
            return [hdr("SKU"), hdr("CÓDIGO"), hdr(""), hdr("MODELO", TA_LEFT), hdr("PREÇO"), hdr("QTD")]
        else:
            return [hdr("CÓDIGO"), hdr(""), hdr("MODELO", TA_LEFT), hdr("PREÇO")]

    def _make_table(self, rows, col_widths, mostrar_sku, is_continuation=False):
        img_col   = 1 if not mostrar_sku else 2
        preco_col = len(col_widths) - (2 if mostrar_sku else 1)

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
        if mostrar_sku:
            cmds.append(("ALIGN", (-1, 0), (-1, -1), "CENTER"))

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

    def _build_row(self, imp, mostrar_sku):
        if mostrar_sku:
            return [self._sku_cell(imp), self._cod_cell(imp),
                    self._img_cell(imp), self._modelo_cell(imp),
                    self._preco_cell(imp, mostrar_sku), self._qtd_cell(imp)]
        else:
            return [self._cod_cell(imp), self._img_cell(imp),
                    self._modelo_cell(imp), self._preco_cell(imp, mostrar_sku)]

    def _sku_cell(self, imp):
        sku = imp.get("sku", "").strip()
        return Paragraph(sku or "—", ParagraphStyle(
            "ISKU", fontName="Helvetica-Bold", fontSize=10,
            textColor=AZUL_SKU, alignment=TA_CENTER, leading=14))

    def _cod_cell(self, imp):
        cod = imp.get("marca", "").strip()
        return Paragraph(cod or "—", ParagraphStyle(
            "ICod", fontName="Helvetica-Bold", fontSize=12,
            textColor=PRETO, alignment=TA_CENTER, leading=16))

    def _img_cell(self, imp):
        img_path = imp.get("imagem_path", "")
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

    def _modelo_cell(self, imp):
        modelo = imp.get("modelo", "").strip()
        return Paragraph(modelo, ParagraphStyle(
            "IModelo", fontName="Helvetica", fontSize=13,
            textColor=PRETO, leading=16, leftIndent=6))

    def _qtd_cell(self, imp):
        qtd = imp.get("quantidade", "").strip()
        return Paragraph(qtd or "—", ParagraphStyle(
            "IQtd", fontName="Helvetica-Bold", fontSize=12,
            textColor=PRETO, alignment=TA_CENTER, leading=16))

    def _preco_cell(self, imp, mostrar_sku=False):
        em_estoque = bool(imp.get("em_estoque", 1))
        if mostrar_sku and not em_estoque:
            return Paragraph("Esgotado", ParagraphStyle(
                "IEsgotado", fontName="Helvetica-Bold", fontSize=11,
                textColor=VERMELHO, alignment=TA_CENTER, leading=16))
        preco = imp.get("preco", "").strip()
        if preco and not preco.upper().startswith("R$"):
            preco = f"R$ {preco}"
        return Paragraph(preco or "—", ParagraphStyle(
            "IPreco", fontName="Helvetica", fontSize=13,
            textColor=PRETO, alignment=TA_CENTER, leading=16))
