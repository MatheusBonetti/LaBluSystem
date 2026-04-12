"""
Diálogo para cadastrar/editar filamentos.
"""

from pathlib import Path
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QLabel,
    QLineEdit, QPushButton, QComboBox, QFileDialog,
    QMessageBox, QFrame, QWidget, QScrollArea
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap


class FilamentoDialog(QDialog):
    def __init__(self, parent, db, filamento_id=None, categoria_id=None):
        super().__init__(parent)
        self.db = db
        self.filamento_id = filamento_id
        self.editing = filamento_id is not None
        self.imagem_path = ""
        self.selected_image_source = ""

        title = "Editar Filamento" if self.editing else "Novo Filamento"
        self.setWindowTitle(title)
        self.setModal(True)
        self.setMinimumSize(520, 520)
        self.resize(540, 540)

        self._build_ui()
        self._load_categorias(categoria_id)

        if self.editing:
            self._load_filamento_data()

    def _build_ui(self):
        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        container = QWidget()
        scroll.setWidget(container)

        main = QVBoxLayout(container)
        main.setContentsMargins(24, 20, 24, 20)
        main.setSpacing(16)

        # ── Imagem ──
        img_label = QLabel("Imagem do Filamento")
        img_label.setStyleSheet("font-weight: 700; font-size: 13px; color: #1a6ef0; letter-spacing: 1px;")
        main.addWidget(img_label)

        img_row = QHBoxLayout()
        self.img_preview = QLabel()
        self.img_preview.setFixedSize(100, 100)
        self.img_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.img_preview.setStyleSheet(
            "background-color: #f0f2f7; border-radius: 8px; border: 1px solid #dde1ea; color: #9aa0b0; font-size: 28px;"
        )
        self.img_preview.setText("📷")

        img_btns = QVBoxLayout()
        select_img_btn = QPushButton("Selecionar Imagem")
        select_img_btn.clicked.connect(self._select_image)
        clear_img_btn = QPushButton("Remover")
        clear_img_btn.setProperty("flat", True)
        clear_img_btn.clicked.connect(self._clear_image)
        img_btns.addWidget(select_img_btn)
        img_btns.addWidget(clear_img_btn)
        img_btns.addStretch()

        img_row.addWidget(self.img_preview)
        img_row.addSpacing(16)
        img_row.addLayout(img_btns)
        img_row.addStretch()
        main.addLayout(img_row)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("background-color: #dde1ea; border: none; max-height: 1px;")
        main.addWidget(sep)

        form_label = QLabel("Informações do Filamento")
        form_label.setStyleSheet("font-weight: 700; font-size: 13px; color: #1a6ef0; letter-spacing: 1px;")
        main.addWidget(form_label)

        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        form.setSpacing(10)
        form.setContentsMargins(0, 0, 0, 0)

        self.cat_combo = QComboBox()
        form.addRow("Categoria *:", self.cat_combo)

        self.nome_input = QLineEdit()
        self.nome_input.setPlaceholderText("Ex: Orange, Blue, Candy Red...")
        form.addRow("Cor *:", self.nome_input)

        self.sku_input = QLineEdit()
        self.sku_input.setPlaceholderText("Ex: FIL-001, SKU-2024...")
        form.addRow("SKU:", self.sku_input)

        self.marca_input = QLineEdit()
        self.marca_input.setPlaceholderText("Ex: 10300, 10103...")
        form.addRow("Código:", self.marca_input)


        self.preco_input = QLineEdit()
        self.preco_input.setPlaceholderText("Ex: R$ 140,00")
        form.addRow("Preço:", self.preco_input)

        self.quantidade_input = QLineEdit()
        self.quantidade_input.setPlaceholderText("Ex: 5")
        form.addRow("Quantidade:", self.quantidade_input)

        main.addLayout(form)
        main.addStretch()

        btn_row = QHBoxLayout()
        cancel_btn = QPushButton("Cancelar")
        cancel_btn.setProperty("flat", True)
        cancel_btn.clicked.connect(self.reject)
        self.save_btn = QPushButton("Salvar Filamento")
        self.save_btn.clicked.connect(self._save)
        btn_row.addWidget(cancel_btn)
        btn_row.addWidget(self.save_btn)
        main.addLayout(btn_row)

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.addWidget(scroll)

    def _load_categorias(self, default_id=None):
        self.cat_combo.clear()
        categorias = self.db.get_categorias()
        for cat in categorias:
            self.cat_combo.addItem(cat["nome"], cat["id"])
        if default_id is not None:
            for i in range(self.cat_combo.count()):
                if self.cat_combo.itemData(i) == default_id:
                    self.cat_combo.setCurrentIndex(i)
                    break

    def _load_filamento_data(self):
        fil = self.db.get_filamento(self.filamento_id)
        if not fil:
            return

        for i in range(self.cat_combo.count()):
            if self.cat_combo.itemData(i) == fil["categoria_id"]:
                self.cat_combo.setCurrentIndex(i)
                break

        self.nome_input.setText(fil.get("nome", ""))
        self.sku_input.setText(fil.get("sku", ""))
        self.marca_input.setText(fil.get("marca", ""))

        self.preco_input.setText(fil.get("peso_total", ""))
        self.quantidade_input.setText(fil.get("quantidade", ""))

        img = fil.get("imagem_path", "")
        if img and Path(img).exists():
            self.imagem_path = img
            self._show_preview(img)

    def _select_image(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Selecionar Imagem", "",
            "Imagens (*.png *.jpg *.jpeg *.bmp *.webp *.gif)"
        )
        if path:
            self.selected_image_source = path
            self._show_preview(path)

    def _clear_image(self):
        self.selected_image_source = ""
        self.imagem_path = ""
        self.img_preview.setPixmap(QPixmap())
        self.img_preview.setText("📷")

    def _show_preview(self, path):
        pix = QPixmap(path)
        if not pix.isNull():
            scaled = pix.scaled(100, 100, Qt.AspectRatioMode.KeepAspectRatio,
                                Qt.TransformationMode.SmoothTransformation)
            self.img_preview.setText("")
            self.img_preview.setPixmap(scaled)

    def _save(self):
        nome = self.nome_input.text().strip()
        if not nome:
            QMessageBox.warning(self, "Campo obrigatório", "O nome do filamento é obrigatório.")
            return

        cat_id = self.cat_combo.currentData()
        if cat_id is None:
            QMessageBox.warning(self, "Campo obrigatório", "Selecione uma categoria.")
            return

        dados = {
            "categoria_id": cat_id,
            "nome": nome,
            "sku": self.sku_input.text(),
            "marca": self.marca_input.text(),
            "cor": "",
            "diametro": "1.75mm",
            "temperatura_bico": "",
            "temperatura_cama": "",
            "peso_total": self.preco_input.text(),
            "quantidade": self.quantidade_input.text(),
            "peso_restante": "",
            "notas": "",
            "imagem_path": self.imagem_path,
        }

        if self.editing:
            if self.selected_image_source:
                saved = self.db.save_image(self.selected_image_source, self.filamento_id)
                dados["imagem_path"] = saved
            self.db.update_filamento(self.filamento_id, dados)
        else:
            new_id = self.db.add_filamento(dados)
            if self.selected_image_source:
                saved = self.db.save_image(self.selected_image_source, new_id)
                dados["imagem_path"] = saved
                self.db.update_filamento(new_id, dados)

        self.accept()