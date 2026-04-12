"""
Diálogo para criar/editar categorias.
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QMessageBox
)
from PyQt6.QtCore import Qt


class CategoriaDialog(QDialog):
    def __init__(self, parent, db, nome_atual="", categoria_id=None, add_fn=None, update_fn=None):
        super().__init__(parent)
        self.db = db
        self.categoria_id = categoria_id
        self.editing = categoria_id is not None
        self._add_fn = add_fn if add_fn is not None else db.add_categoria
        self._update_fn = update_fn if update_fn is not None else db.update_categoria

        title = "Editar Categoria" if self.editing else "Nova Categoria"
        self.setWindowTitle(title)
        self.setModal(True)
        self.setFixedSize(400, 160)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(14)

        label = QLabel("Nome da categoria:")
        layout.addWidget(label)

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Ex: PETG-HF, PLA BASIC, ABS...")
        self.name_input.setText(nome_atual)
        self.name_input.returnPressed.connect(self._save)
        layout.addWidget(self.name_input)

        btn_row = QHBoxLayout()
        cancel_btn = QPushButton("Cancelar")
        cancel_btn.setProperty("flat", True)
        cancel_btn.clicked.connect(self.reject)
        save_btn = QPushButton("Salvar")
        save_btn.clicked.connect(self._save)
        btn_row.addWidget(cancel_btn)
        btn_row.addWidget(save_btn)
        layout.addLayout(btn_row)

        self.name_input.setFocus()
        self.name_input.selectAll()

    def _save(self):
        nome = self.name_input.text().strip()
        if not nome:
            QMessageBox.warning(self, "Campo obrigatório", "Digite o nome da categoria.")
            return

        if self.editing:
            ok, msg = self._update_fn(self.categoria_id, nome)
        else:
            ok, msg = self._add_fn(nome)

        if ok:
            self.accept()
        else:
            QMessageBox.warning(self, "Erro", msg)