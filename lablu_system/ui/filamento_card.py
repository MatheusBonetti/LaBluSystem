"""
Card visual para exibição de filamento em lista compacta.
"""

from pathlib import Path
from PyQt6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QPushButton, QWidget, QCheckBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QPixmap, QCursor

COL_ESTOQUE = 70
COL_IMG     = 52
COL_SKU     = 55
COL_CODIGO  = 120
COL_COR     = 200
COL_CAT     = 180
COL_PRECO   = 110
COL_QTD     = 110


class _ImageHoverLabel(QLabel):
    """Label que exibe um popup com a imagem ampliada ao passar o mouse."""

    def __init__(self, img_path: str, parent=None):
        super().__init__(parent)
        self._img_path = img_path
        self._popup = None

    def enterEvent(self, event):
        if self._img_path and Path(self._img_path).exists():
            self._show_popup()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._hide_popup()
        super().leaveEvent(event)

    def _show_popup(self):
        pix = QPixmap(self._img_path)
        if pix.isNull():
            return
        scaled = pix.scaled(210, 210,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation)

        self._popup = QLabel()
        self._popup.setWindowFlags(
            Qt.WindowType.ToolTip |
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint
        )
        self._popup.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self._popup.setPixmap(scaled)
        self._popup.setStyleSheet(
            "background: white;"
            "border: 2px solid #4F9900;"
            "border-radius: 10px;"
            "padding: 6px;"
        )
        self._popup.adjustSize()
        pos = QCursor.pos()
        self._popup.move(pos.x() + 20, pos.y() - self._popup.height() // 2)
        self._popup.show()

    def _hide_popup(self):
        if self._popup:
            self._popup.hide()
            self._popup.deleteLater()
            self._popup = None


class FilamentoCard(QFrame):
    edit_requested   = pyqtSignal(int)
    delete_requested = pyqtSignal(int)
    selection_toggled = pyqtSignal(int, bool)   # (filamento_id, is_selected)

    def __init__(self, filamento: dict, db, pixmap_cache: dict = None):
        super().__init__()
        self.filamento = filamento
        self.db = db
        self._pixmap_cache = pixmap_cache if pixmap_cache is not None else {}
        self._in_selection_mode = False
        self._is_selected = False
        self.setObjectName("filCard")
        self._build()

    # ── Seleção ──────────────────────────────────────────────────────────────

    def set_selection_mode(self, enabled: bool):
        self._in_selection_mode = enabled
        if not enabled:
            self._is_selected = False
        self._update_visual(bool(self.filamento.get("em_estoque", 1)))
        self.setCursor(
            Qt.CursorShape.PointingHandCursor if enabled
            else Qt.CursorShape.ArrowCursor
        )

    def mousePressEvent(self, event):
        if self._in_selection_mode and event.button() == Qt.MouseButton.LeftButton:
            self._is_selected = not self._is_selected
            self._update_visual(bool(self.filamento.get("em_estoque", 1)))
            self.selection_toggled.emit(self.filamento["id"], self._is_selected)
        super().mousePressEvent(event)

    # ── Construção ───────────────────────────────────────────────────────────

    def _build(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(0)

        # ── Estoque (checkbox) ──────────────────────────────────────────
        em_estoque = bool(self.filamento.get("em_estoque", 1))
        self.estoque_cb = QCheckBox()
        self.estoque_cb.setChecked(em_estoque)
        self.estoque_cb.setToolTip("Marcado = Em estoque | Desmarcado = Esgotado")
        self.estoque_cb.stateChanged.connect(self._on_estoque_changed)

        estoque_wrap = QWidget()
        estoque_wrap.setFixedWidth(COL_ESTOQUE)
        ew = QHBoxLayout(estoque_wrap)
        ew.setContentsMargins(0, 0, 8, 0)
        ew.setAlignment(Qt.AlignmentFlag.AlignCenter)
        ew.addWidget(self.estoque_cb)
        layout.addWidget(estoque_wrap)

        # ── SKU ─────────────────────────────────────────────────────────
        sku_lbl = QLabel(self.filamento.get("sku", "").strip() or "—")
        sku_lbl.setObjectName("cardBrand")
        sku_lbl.setFixedWidth(COL_SKU)
        sku_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(sku_lbl)

        # ── Código ──────────────────────────────────────────────────────
        cod_lbl = QLabel(self.filamento.get("marca", "").strip() or "—")
        cod_lbl.setObjectName("cardBrand")
        cod_lbl.setFixedWidth(COL_CODIGO)
        cod_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(cod_lbl)

        # ── Imagem (com hover preview) ──────────────────────────────────
        img_path = self.filamento.get("imagem_path", "")
        img_label = _ImageHoverLabel(img_path)
        img_label.setFixedSize(44, 44)
        img_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        if img_path and Path(img_path).exists():
            if img_path not in self._pixmap_cache:
                raw = QPixmap(img_path)
                self._pixmap_cache[img_path] = raw.scaled(
                    44, 44,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                ) if not raw.isNull() else raw
            pix = self._pixmap_cache[img_path]
            if not pix.isNull():
                img_label.setPixmap(pix)
                img_label.setObjectName("cardImage")
            else:
                img_label.setText("🧵")
                img_label.setObjectName("noImageLabel")
        else:
            img_label.setText("🧵")
            img_label.setObjectName("noImageLabel")

        img_wrap = QWidget()
        img_wrap.setFixedWidth(COL_IMG)
        iw = QHBoxLayout(img_wrap)
        iw.setContentsMargins(0, 0, 8, 0)
        iw.addWidget(img_label)
        layout.addWidget(img_wrap)

        # ── Cor ─────────────────────────────────────────────────────────
        cor_lbl = QLabel(self.filamento.get("nome", "").strip())
        cor_lbl.setObjectName("cardName")
        cor_lbl.setFixedWidth(COL_COR)
        cor_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(cor_lbl)

        # ── Preço ───────────────────────────────────────────────────────
        preco = self.filamento.get("peso_total", "").strip()
        if preco and not preco.upper().startswith("R$"):
            preco = f"R$ {preco}"
        preco_lbl = QLabel(preco if preco else "—")
        preco_lbl.setObjectName("cardPreco")
        preco_lbl.setFixedWidth(COL_PRECO)
        preco_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(preco_lbl)

        # ── Quantidade ──────────────────────────────────────────────────
        qtd = self.filamento.get("quantidade", "").strip()
        qtd_lbl = QLabel(qtd if qtd else "—")
        qtd_lbl.setObjectName("cardQtd")
        qtd_lbl.setFixedWidth(COL_QTD)
        qtd_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(qtd_lbl)

        layout.addStretch()

        # ── Ações ───────────────────────────────────────────────────────
        edit_btn = QPushButton("Editar")
        edit_btn.setObjectName("cardEditBtn")
        edit_btn.setFixedWidth(84)
        edit_btn.clicked.connect(lambda: self.edit_requested.emit(self.filamento["id"]))

        del_btn = QPushButton("✕")
        del_btn.setObjectName("cardDeleteBtn")
        del_btn.setFixedWidth(32)
        del_btn.clicked.connect(lambda: self.delete_requested.emit(self.filamento["id"]))

        layout.addWidget(edit_btn)
        layout.addSpacing(6)
        layout.addWidget(del_btn)

        self._update_visual(em_estoque)

    def _on_estoque_changed(self, state):
        em_estoque = (state == Qt.CheckState.Checked.value)
        self.db.set_estoque(self.filamento["id"], em_estoque)
        self.filamento["em_estoque"] = 1 if em_estoque else 0
        self._update_visual(em_estoque)

    def _update_visual(self, em_estoque: bool):
        if self._is_selected:
            self.setStyleSheet("""
                #filCard {
                    background-color: #f0f9e8;
                    border: 1px solid #b8dfa0;
                    border-left: 4px solid #4F9900;
                    border-radius: 8px;
                }
            """)
        elif em_estoque:
            self.setStyleSheet("")
        else:
            self.setStyleSheet("""
                #filCard {
                    background-color: #f8f8f8;
                    border: 1px solid #e0e0e0;
                    border-radius: 8px;
                }
                QLabel { color: #aaaaaa; }
            """)
