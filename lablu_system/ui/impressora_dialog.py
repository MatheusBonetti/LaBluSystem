"""
Diálogo para cadastrar/editar impressoras.
"""

from pathlib import Path
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QLabel,
    QLineEdit, QPushButton, QComboBox, QFileDialog,
    QMessageBox, QFrame, QWidget, QScrollArea
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap


class ImpressoraDialog(QDialog):
    def __init__(self, parent, db, impressora_id=None, categoria_id=None):
        super().__init__(parent)
        self.db = db
        self.impressora_id = impressora_id
        self.editing = impressora_id is not None
        self.imagem_path = ""
        self.selected_image_source = ""

        self.setWindowTitle("Editar Impressora" if self.editing else "Nova Impressora")
        self.setModal(True)
        self.setMinimumSize(520, 540)
        self.resize(540, 540)

        self._build_ui()
        self._load_categorias(categoria_id)

        if self.editing:
            self._load_impressora_data()

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
        img_label = QLabel("Imagem da Impressora")
        img_label.setStyleSheet("font-weight: 700; font-size: 13px; color: #1a6ef0; letter-spacing: 1px;")
        main.addWidget(img_label)

        img_row = QHBoxLayout()
        self.img_preview = QLabel()
        self.img_preview.setFixedSize(100, 100)
        self.img_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.img_preview.setStyleSheet(
            "background-color: #f0f2f7; border-radius: 8px; border: 1px solid #dde1ea; color: #9aa0b0; font-size: 28px;"
        )
        self.img_preview.setText("🖨️")

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

        form_label = QLabel("Informações da Impressora")
        form_label.setStyleSheet("font-weight: 700; font-size: 13px; color: #1a6ef0; letter-spacing: 1px;")
        main.addWidget(form_label)

        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        form.setSpacing(10)
        form.setContentsMargins(0, 0, 0, 0)

        self.cat_combo = QComboBox()
        form.addRow("Categoria *:", self.cat_combo)

        self.modelo_input = QLineEdit()
        self.modelo_input.setPlaceholderText("Ex: X1C, P1S, A1 Mini...")
        form.addRow("Modelo *:", self.modelo_input)

        self.sku_input = QLineEdit()
        self.sku_input.setPlaceholderText("Ex: IMP-001...")
        form.addRow("SKU:", self.sku_input)

        self.marca_input = QLineEdit()
        self.marca_input.setPlaceholderText("Ex: Bambu Lab, Creality...")
        form.addRow("Código:", self.marca_input)

        self.preco_input = QLineEdit()
        self.preco_input.setPlaceholderText("Ex: R$ 4.500,00")
        form.addRow("Preço:", self.preco_input)

        self.quantidade_input = QLineEdit()
        self.quantidade_input.setPlaceholderText("Ex: 3")
        form.addRow("Quantidade:", self.quantidade_input)

        main.addLayout(form)
        main.addStretch()

        btn_row = QHBoxLayout()
        cancel_btn = QPushButton("Cancelar")
        cancel_btn.setProperty("flat", True)
        cancel_btn.clicked.connect(self.reject)
        self.save_btn = QPushButton("Salvar Impressora")
        self.save_btn.clicked.connect(self._save)
        btn_row.addWidget(cancel_btn)
        btn_row.addWidget(self.save_btn)
        main.addLayout(btn_row)

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.addWidget(scroll)

    def _load_categorias(self, default_id=None):
        self.cat_combo.clear()
        for cat in self.db.get_categorias_impressoras():
            self.cat_combo.addItem(cat["nome"], cat["id"])
        if default_id is not None:
            for i in range(self.cat_combo.count()):
                if self.cat_combo.itemData(i) == default_id:
                    self.cat_combo.setCurrentIndex(i)
                    break

    def _load_impressora_data(self):
        imp = self.db.get_impressora(self.impressora_id)
        if not imp:
            return
        for i in range(self.cat_combo.count()):
            if self.cat_combo.itemData(i) == imp["categoria_id"]:
                self.cat_combo.setCurrentIndex(i)
                break
        self.modelo_input.setText(imp.get("modelo", ""))
        self.sku_input.setText(imp.get("sku", ""))
        self.marca_input.setText(imp.get("marca", ""))
        self.preco_input.setText(imp.get("preco", ""))
        self.quantidade_input.setText(imp.get("quantidade", ""))
        img = imp.get("imagem_path", "")
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
        self.img_preview.setText("🖨️")

    def _show_preview(self, path):
        pix = QPixmap(path)
        if not pix.isNull():
            scaled = pix.scaled(100, 100, Qt.AspectRatioMode.KeepAspectRatio,
                                Qt.TransformationMode.SmoothTransformation)
            self.img_preview.setText("")
            self.img_preview.setPixmap(scaled)

    def _save(self):
        modelo = self.modelo_input.text().strip()
        if not modelo:
            QMessageBox.warning(self, "Campo obrigatório", "O modelo da impressora é obrigatório.")
            return
        cat_id = self.cat_combo.currentData()
        if cat_id is None:
            QMessageBox.warning(self, "Campo obrigatório", "Selecione uma categoria.")
            return

        dados = {
            "categoria_id": cat_id,
            "modelo": modelo,
            "sku": self.sku_input.text(),
            "marca": self.marca_input.text(),
            "preco": self.preco_input.text(),
            "quantidade": self.quantidade_input.text(),
            "imagem_path": self.imagem_path,
        }

        if self.editing:
            if self.selected_image_source:
                saved = self.db.save_impressora_image(self.selected_image_source, self.impressora_id)
                dados["imagem_path"] = saved
            self.db.update_impressora(self.impressora_id, dados)
        else:
            new_id = self.db.add_impressora(dados)
            if self.selected_image_source:
                saved = self.db.save_impressora_image(self.selected_image_source, new_id)
                dados["imagem_path"] = saved
                self.db.update_impressora(new_id, dados)

        self.accept()
