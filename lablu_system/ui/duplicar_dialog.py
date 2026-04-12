"""
Diálogo de configuração antes de duplicar filamentos.
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QLineEdit, QComboBox, QPushButton, QFrame
)
from PyQt6.QtCore import Qt


class DuplicarDialog(QDialog):
    def __init__(self, parent, db, quantidade: int, get_categorias_fn=None, item_label="filamento"):
        super().__init__(parent)
        self.db = db
        self.quantidade = quantidade
        self._get_categorias = get_categorias_fn if get_categorias_fn is not None else db.get_categorias
        self._item_label = item_label
        self.setWindowTitle("Duplicar")
        self.setModal(True)
        self.setFixedSize(420, 240)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(16)

        # Título
        n = self.quantidade
        label = self._item_label
        titulo = QLabel(f"Duplicando {n} {label}{'s' if n != 1 else ''}")
        titulo.setStyleSheet("font-size: 15px; font-weight: 700; color: #1a1f36;")
        layout.addWidget(titulo)

        desc = QLabel("Defina a categoria e o preço para as cópias.\nDeixe em branco para manter os valores originais.")
        desc.setStyleSheet("color: #5a6070; font-size: 12px;")
        desc.setWordWrap(True)
        layout.addWidget(desc)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("background: #dde1ea; border: none; max-height: 1px;")
        layout.addWidget(sep)

        form = QFormLayout()
        form.setSpacing(10)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        # Categoria
        self.cat_combo = QComboBox()
        self.cat_combo.addItem("— Manter original —", None)
        for cat in self._get_categorias():
            self.cat_combo.addItem(cat["nome"], cat["id"])
        form.addRow("Categoria:", self.cat_combo)

        # Preço
        self.preco_input = QLineEdit()
        self.preco_input.setPlaceholderText("Ex: R$ 140,00  (deixe vazio para manter)")
        form.addRow("Preço:", self.preco_input)

        layout.addLayout(form)
        layout.addStretch()

        # Botões
        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)

        cancel_btn = QPushButton("Cancelar")
        cancel_btn.setProperty("flat", True)
        cancel_btn.clicked.connect(self.reject)

        self.confirm_btn = QPushButton(f"Duplicar")
        self.confirm_btn.clicked.connect(self.accept)

        btn_row.addWidget(cancel_btn)
        btn_row.addWidget(self.confirm_btn)
        layout.addLayout(btn_row)

    def get_values(self):
        """Retorna (categoria_id | None, preco | None)."""
        cat_id = self.cat_combo.currentData()
        preco = self.preco_input.text().strip() or None
        return cat_id, preco
