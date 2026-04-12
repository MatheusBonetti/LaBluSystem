"""
Diálogo para alterar campos de múltiplos itens selecionados.
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QLineEdit, QComboBox, QPushButton, QFrame
)
from PyQt6.QtCore import Qt


class AlterarValoresDialog(QDialog):
    def __init__(self, parent, quantidade: int, get_categorias_fn, item_label="filamento"):
        super().__init__(parent)
        self._get_categorias = get_categorias_fn
        self.quantidade = quantidade
        self._item_label = item_label
        self.setWindowTitle("Alterar Valores")
        self.setModal(True)
        self.setFixedSize(440, 270)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(14)

        n = self.quantidade
        label = self._item_label
        titulo = QLabel(f"Alterando {n} {label}{'s' if n != 1 else ''}")
        titulo.setStyleSheet("font-size: 15px; font-weight: 700; color: #1a1f36;")
        layout.addWidget(titulo)

        desc = QLabel("Preencha apenas os campos que deseja alterar.\nCampos em branco serão mantidos como estão.")
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

        self.cat_combo = QComboBox()
        self.cat_combo.addItem("— Manter original —", None)
        for cat in self._get_categorias():
            self.cat_combo.addItem(cat["nome"], cat["id"])
        form.addRow("Categoria:", self.cat_combo)

        self.preco_input = QLineEdit()
        self.preco_input.setPlaceholderText("Ex: R$ 140,00  (deixe vazio para manter)")
        form.addRow("Preço:", self.preco_input)

        self.quantidade_input = QLineEdit()
        self.quantidade_input.setPlaceholderText("Ex: 5  (deixe vazio para manter)")
        form.addRow("Quantidade:", self.quantidade_input)

        layout.addLayout(form)
        layout.addStretch()

        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)

        cancel_btn = QPushButton("Cancelar")
        cancel_btn.setProperty("flat", True)
        cancel_btn.clicked.connect(self.reject)

        confirm_btn = QPushButton("Aplicar")
        confirm_btn.clicked.connect(self.accept)

        btn_row.addWidget(cancel_btn)
        btn_row.addWidget(confirm_btn)
        layout.addLayout(btn_row)

    def get_values(self):
        """Retorna dict com apenas os campos a alterar (None = não alterar)."""
        result = {}
        cat_id = self.cat_combo.currentData()
        if cat_id is not None:
            result["categoria_id"] = cat_id
        preco = self.preco_input.text().strip()
        if preco:
            result["preco"] = preco
        qtd = self.quantidade_input.text().strip()
        if qtd:
            result["quantidade"] = qtd
        return result
