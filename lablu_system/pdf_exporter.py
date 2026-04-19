"""
Exportador de PDF do LaBlu System.
mostrar_sku=True  → Exportar Loja  (SKU + Código + Cor + Preço/Esgotado)
mostrar_sku=False → Exportar Cliente (só filamentos em estoque, sem SKU)
"""

import math
from datetime import date
from pathlib import Path
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph, Spacer, Table, TableStyle,
    Image, KeepTogether, AnchorFlowable, PageBreak
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
import io

# Pontos disponíveis para as linhas do índice numa página A4 (estimativa conservadora)
_TOC_ROW_AREA = 590

PAGE_W, PAGE_H = A4
MARGIN    = 1.5 * cm
CONTENT_W = PAGE_W - 2 * MARGIN

PRETO        = colors.HexColor("#1a1a1a")
CINZA_BORDA  = colors.HexColor("#bbbbbb")
CINZA_LINHA  = colors.HexColor("#f5f5f5")
CINZA_HEAD   = colors.HexColor("#e8e8e8")
BRANCO       = colors.white
VERDE        = colors.HexColor("#4F9900")
VERDE_CLARO  = colors.HexColor("#f2f8ea")
VERDE_ESCURO = colors.HexColor("#2d6a00")
CINZA_TEXTO  = colors.HexColor("#666666")
AZUL_SKU     = colors.HexColor("#1a6ef0")
VERMELHO     = colors.HexColor("#e02d2d")

IMG_PX = 56
IMG_Q  = 72


def _compress_image(path: str) -> str | None:
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


class _CollectorDoc(SimpleDocTemplate):
    """Primeira passagem: registra a página de cada AnchorFlowable."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._toc_pages: dict[str, int] = {}

    def afterFlowable(self, flowable):
        if isinstance(flowable, AnchorFlowable):
            self._toc_pages[flowable._name] = self.page


class PDFExporter:
    def __init__(self, db):
        self.db = db

    def export(self, output_path: str, mostrar_sku: bool = False):
        cats_com_fil = []
        for cat in self.db.get_categorias():
            fils = self.db.get_filamentos(
                categoria_id=cat["id"],
                apenas_em_estoque=not mostrar_sku,
            )
            if fils:
                cats_com_fil.append((cat, fils))

        if not cats_com_fil:
            return

        col_widths = self._col_widths(mostrar_sku)

        # ── Passagem 1: só o conteúdo, sem TOC (mais rápido e sem conflito) ──
        buf = io.BytesIO()
        collector = _CollectorDoc(
            buf, pagesize=A4,
            leftMargin=MARGIN, rightMargin=MARGIN,
            topMargin=1.5 * cm, bottomMargin=1.5 * cm,
        )
        collector.build(self._build_content_story(cats_com_fil, col_widths, mostrar_sku))
        # +1 em todas as páginas porque o TOC ocupa a página 1
        toc_pages = {k: v + 1 for k, v in collector._toc_pages.items()}

        # ── Passagem 2: TOC + conteúdo → arquivo final ────────────────
        doc = SimpleDocTemplate(
            output_path,
            pagesize=A4,
            leftMargin=MARGIN, rightMargin=MARGIN,
            topMargin=1.5 * cm, bottomMargin=1.5 * cm,
            title="LaBlu System — Catálogo de Filamentos",
            author="LaBlu System",
            compress=1,
        )
        doc.build(self._build_full_story(cats_com_fil, col_widths, mostrar_sku, toc_pages))

    # ── Story completo ────────────────────────────────────────────────

    def _build_content_story(self, cats_com_fil, col_widths, mostrar_sku):
        """Apenas o conteúdo (sem TOC) — usado na passagem 1 para coletar páginas."""
        story = []
        for cat, filamentos in cats_com_fil:
            story.append(AnchorFlowable(f"cat_{cat['id']}"))
            banner    = self._build_banner(cat["nome"])
            data_rows = [self._build_row(fil, mostrar_sku) for fil in filamentos]

            primeiras = [self._build_header_row(mostrar_sku)] + data_rows[:2]
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
        return story

    def _build_full_story(self, cats_com_fil, col_widths, mostrar_sku, toc_pages):
        """TOC + conteúdo — usado na passagem 2 (render final)."""
        story = []
        story += self._build_toc_page(cats_com_fil, mostrar_sku, toc_pages)
        story.append(PageBreak())

        for cat, filamentos in cats_com_fil:
            story.append(AnchorFlowable(f"cat_{cat['id']}"))
            banner    = self._build_banner(cat["nome"])
            data_rows = [self._build_row(fil, mostrar_sku) for fil in filamentos]

            primeiras = [self._build_header_row(mostrar_sku)] + data_rows[:2]
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
        return story

    # ── Página de índice ──────────────────────────────────────────────

    @staticmethod
    def _toc_layout(n):
        """Retorna (cols, fsize, leading, pad) que cabem em 1 página."""
        AVAIL = 560  # pontos disponíveis para linhas (conservador)
        for cols in (1, 2, 3):
            rows = math.ceil(n / cols)
            for fsize, leading in ((11, 15), (9, 12), (8, 10)):
                for pad in (9, 6, 4, 2):
                    if rows * (leading + 2 * pad) <= AVAIL:
                        return cols, fsize, leading, pad
        return 3, 8, 10, 2

    @staticmethod
    def _trunc(text, maxchars):
        return text if len(text) <= maxchars else text[:maxchars - 1] + "…"

    def _build_toc_page(self, cats_com_fil, mostrar_sku, toc_pages):
        elements = []
        n_cats   = len(cats_com_fil)
        cols, fsize, leading, pad = self._toc_layout(n_cats)

        # ── Cabeçalho verde ───────────────────────────────────────────
        titulo = "Catálogo de Filamentos — Loja" if mostrar_sku else "Catálogo de Filamentos - BambuLaBlu"
        s_titulo = ParagraphStyle("TT", fontName="Helvetica-Bold", fontSize=22,
                                  textColor=BRANCO, alignment=TA_CENTER, leading=28)
        s_data   = ParagraphStyle("TD", fontName="Helvetica", fontSize=10,
                                  textColor=colors.HexColor("#d4edaa"), alignment=TA_CENTER, leading=14)
        hoje = date.today().strftime("%d/%m/%Y")

        hdr = Table([
            [Paragraph(titulo, s_titulo)],
            [Paragraph(f"LaBlu System  ·  {hoje}", s_data)],
        ], colWidths=[CONTENT_W])
        hdr.setStyle(TableStyle([
            ("BACKGROUND",    (0, 0), (-1, -1), VERDE),
            ("TOPPADDING",    (0, 0), (-1, 0),  22),
            ("BOTTOMPADDING", (0, 0), (-1, 0),  4),
            ("TOPPADDING",    (0, 1), (-1, 1),  0),
            ("BOTTOMPADDING", (0, 1), (-1, 1),  18),
            ("LEFTPADDING",   (0, 0), (-1, -1), 0),
            ("RIGHTPADDING",  (0, 0), (-1, -1), 0),
        ]))
        elements.append(hdr)
        elements.append(Spacer(1, 0.6 * cm))

        s_label = ParagraphStyle("TL", fontName="Helvetica-Bold", fontSize=8,
                                 textColor=CINZA_TEXTO, alignment=TA_LEFT, leading=12,
                                 letterSpacing=2)
        elements.append(Paragraph("CLIQUE NO TIPO DE MATERIAL DESEJADO", s_label))
        elements.append(Spacer(1, 0.2 * cm))

        sep_tbl = Table([[""]], colWidths=[CONTENT_W])
        sep_tbl.setStyle(TableStyle([
            ("LINEBELOW",     (0, 0), (-1, -1), 1.5, VERDE),
            ("TOPPADDING",    (0, 0), (-1, -1), 0),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
            ("LEFTPADDING",   (0, 0), (-1, -1), 0),
            ("RIGHTPADDING",  (0, 0), (-1, -1), 0),
        ]))
        elements.append(sep_tbl)
        elements.append(Spacer(1, 0.15 * cm))

        # ── Geometria das colunas ─────────────────────────────────────
        GAP_W  = 0.5 * cm   # separador entre grupos de colunas
        PL, PR = 10, 6      # padding esq/dir nas células de dados

        if cols == 1:
            C_PG  = 1.8 * cm
            C_CNT = 2.8 * cm
            C_NM  = CONTENT_W - C_PG - C_CNT
            col_widths = [C_NM, C_CNT, C_PG]
            max_chars  = 60
        elif cols == 2:
            HALF  = (CONTENT_W - GAP_W) / 2
            C_PG  = 1.5 * cm
            C_CNT = 2.3 * cm
            C_NM  = HALF - C_PG - C_CNT
            col_widths = [C_NM, C_CNT, C_PG, GAP_W, C_NM, C_CNT, C_PG]
            max_chars  = max(12, int((C_NM - PL - PR) / (fsize * 0.55)))
        else:
            THIRD = (CONTENT_W - 2 * GAP_W) / 3
            C_PG  = 1.2 * cm
            C_CNT = 1.8 * cm
            C_NM  = THIRD - C_PG - C_CNT
            col_widths = [C_NM, C_CNT, C_PG, GAP_W, C_NM, C_CNT, C_PG, GAP_W, C_NM, C_CNT, C_PG]
            max_chars  = max(8, int((C_NM - PL - PR) / (fsize * 0.6)))

        # ── Estilos ───────────────────────────────────────────────────
        s_nm = ParagraphStyle("TNm", fontName="Helvetica-Bold", fontSize=fsize,
                              textColor=VERDE_ESCURO, alignment=TA_LEFT,  leading=leading)
        s_ct = ParagraphStyle("TCt", fontName="Helvetica",      fontSize=max(fsize-2, 6),
                              textColor=CINZA_TEXTO,  alignment=TA_CENTER, leading=leading)
        s_pg = ParagraphStyle("TPg", fontName="Helvetica-Bold", fontSize=fsize,
                              textColor=VERDE,        alignment=TA_CENTER, leading=leading)
        s_gp = ParagraphStyle("TGp", fontSize=fsize, leading=leading)

        def cell(cat, items):
            anchor = f"cat_{cat['id']}"
            pg_val = str(toc_pages.get(anchor, "—")) if toc_pages else "—"
            n      = len(items)
            nome   = self._trunc(cat["nome"], max_chars)
            return (Paragraph(f'<link href="#{anchor}">{nome}</link>', s_nm),
                    Paragraph(f"{n} {'item' if n==1 else 'itens'}", s_ct),
                    Paragraph(pg_val, s_pg))

        empty_nm = Paragraph("", s_nm)
        empty_ct = Paragraph("", s_ct)
        empty_pg = Paragraph("", s_pg)
        gap_cell = Paragraph("", s_gp)

        # ── Monta linhas da tabela flat ───────────────────────────────
        rows_per_col = math.ceil(n_cats / cols)
        flat_rows = []
        for i in range(rows_per_col):
            row = []
            for c in range(cols):
                idx = c * rows_per_col + i
                if idx < n_cats:
                    nm, ct, pg = cell(*cats_com_fil[idx])
                else:
                    nm, ct, pg = empty_nm, empty_ct, empty_pg
                if c > 0:
                    row.append(gap_cell)
                row += [nm, ct, pg]
            flat_rows.append(row)

        # ── Comandos de estilo da tabela flat ─────────────────────────
        n_cols_total = len(col_widths)
        cmds = [
            ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING",    (0, 0), (-1, -1), pad),
            ("BOTTOMPADDING", (0, 0), (-1, -1), pad),
            ("LEFTPADDING",   (0, 0), (-1, -1), PL),
            ("RIGHTPADDING",  (0, 0), (-1, -1), PR),
            ("ROWBACKGROUNDS",(0, 0), (-1, -1), [BRANCO, VERDE_CLARO]),
            ("LINEBELOW",     (0, 0), (-1, -2), 0.4, CINZA_BORDA),
        ]
        # Acento verde à esquerda de cada grupo e padding zero no separador
        for c in range(cols):
            nm_col = c * 4 if c > 0 else 0  # índice da col de nome deste grupo
            if c > 0:
                sep_col = c * 4 - 1
                cmds += [
                    ("LEFTPADDING",  (sep_col, 0), (sep_col, -1), 0),
                    ("RIGHTPADDING", (sep_col, 0), (sep_col, -1), 0),
                    ("TOPPADDING",   (sep_col, 0), (sep_col, -1), 0),
                    ("BOTTOMPADDING",(sep_col, 0), (sep_col, -1), 0),
                ]
            cmds.append(("LINEBEFORE", (nm_col, 0), (nm_col, -1), 3, VERDE))

        flat_tbl = Table(flat_rows, colWidths=col_widths)
        flat_tbl.setStyle(TableStyle(cmds))
        elements.append(flat_tbl)

        # ── Rodapé ────────────────────────────────────────────────────
        elements.append(Spacer(1, 0.35 * cm))
        s_footer = ParagraphStyle("TF", fontName="Helvetica", fontSize=8,
                                  textColor=CINZA_TEXTO, alignment=TA_RIGHT, leading=12)
        elements.append(Paragraph("Clique em uma categoria para ir direto à seção.", s_footer))

        return elements

    # ── Banner ────────────────────────────────────────────────────────

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

    # ── Colunas ───────────────────────────────────────────────────────

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

    # ── Cabeçalho ─────────────────────────────────────────────────────

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

    # ── Tabela ────────────────────────────────────────────────────────

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

    # ── Linha de dados ────────────────────────────────────────────────

    def _build_row(self, fil, mostrar_sku):
        if mostrar_sku:
            return [self._sku_cell(fil), self._cod_cell(fil),
                    self._img_cell(fil), self._nome_cell(fil),
                    self._preco_cell(fil, mostrar_sku), self._qtd_cell(fil)]
        else:
            return [self._cod_cell(fil), self._img_cell(fil),
                    self._nome_cell(fil), self._preco_cell(fil, mostrar_sku)]

    # ── Células ───────────────────────────────────────────────────────

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
