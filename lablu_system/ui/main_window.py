"""
Janela principal do LaBlu System.
"""

import os
import platform
import shutil
import subprocess
import tempfile
import traceback

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QLabel, QPushButton, QListWidget, QListWidgetItem, QFrame,
    QScrollArea, QMessageBox, QStatusBar, QToolButton, QMenu, QLineEdit,
    QFileDialog, QStackedWidget, QAbstractItemView
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QIcon

from ui.styles import STYLE_SHEET, COLORS
from ui.categoria_dialog import CategoriaDialog
from ui.filamento_dialog import FilamentoDialog
from ui.impressora_dialog import ImpressoraDialog
from ui.filamento_card import FilamentoCard, COL_ESTOQUE, COL_IMG, COL_SKU, COL_CODIGO, COL_COR, COL_PRECO, COL_QTD
from ui.impressora_card import ImpressoraCard, COL_MODELO
from ui.duplicar_dialog import DuplicarDialog
from ui.alterar_valores_dialog import AlterarValoresDialog
from pdf_exporter import PDFExporter
from pdf_exporter_impressoras import PDFExporterImpressoras

SIDE_MARGIN = 16


class MainWindow(QMainWindow):
    def __init__(self, db):
        super().__init__()
        self.db = db

        # ── Estado filamentos ──────────────────────────────────────────
        self.current_categoria_id = None
        self._todos_filamentos = []
        self._pixmap_cache = {}
        self._pending_render = []
        self._card_refs = []
        self._selected_ids = set()
        self._selection_mode = False
        self._search_timer = QTimer()
        self._search_timer.setSingleShot(True)
        self._search_timer.setInterval(250)
        self._search_timer.timeout.connect(self._do_search)
        self._search_pending_text = ""

        # ── Estado impressoras ─────────────────────────────────────────
        self._imp_categoria_id = None
        self._imp_todos = []
        self._imp_pending_render = []
        self._imp_card_refs = []
        self._imp_selected_ids = set()
        self._imp_selection_mode = False
        self._imp_search_timer = QTimer()
        self._imp_search_timer.setSingleShot(True)
        self._imp_search_timer.setInterval(250)
        self._imp_search_timer.timeout.connect(self._imp_do_search)
        self._imp_search_pending = ""

        self.setWindowTitle("LaBlu System — Gerenciador da BambuLaBlu")
        self.setMinimumSize(1100, 700)
        self.resize(1280, 800)
        self.setStyleSheet(STYLE_SHEET)

        self._build_ui()
        self._load_categorias()

    # ═══════════════════════════════════════════════════════════════════
    # BUILD UI
    # ═══════════════════════════════════════════════════════════════════

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QHBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        root.addWidget(self._build_sidebar())

        self.content_stack = QStackedWidget()
        self.content_stack.addWidget(self._build_filamentos_content())
        self.content_stack.addWidget(self._build_impressoras_content())
        root.addWidget(self.content_stack, stretch=1)

        self.status_bar = QStatusBar()
        self.status_bar.setObjectName("statusBar")
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Bem-vindo ao LaBlu System!")

    def _build_sidebar(self):
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(240)
        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # ── Logo ──────────────────────────────────────────────────────
        header = QWidget()
        header.setObjectName("sidebarHeader")
        h_layout = QVBoxLayout(header)
        h_layout.setContentsMargins(20, 24, 20, 20)
        logo_label = QLabel("LaBlu")
        logo_label.setObjectName("logoLabel")
        system_label = QLabel("SYSTEM")
        system_label.setObjectName("systemLabel")
        subtitle = QLabel("Gerenciador de Filamentos")
        subtitle.setObjectName("subtitleLabel")
        subtitle.setWordWrap(True)
        h_layout.addWidget(logo_label)
        h_layout.addWidget(system_label)
        h_layout.addWidget(subtitle)
        layout.addWidget(header)

        # ── Navegação ─────────────────────────────────────────────────
        nav = QWidget()
        nav.setStyleSheet("background: #f0f2f7; border-bottom: 1px solid #dde1ea;")
        nav_layout = QHBoxLayout(nav)
        nav_layout.setContentsMargins(8, 8, 8, 8)
        nav_layout.setSpacing(6)

        self.btn_nav_fil = QPushButton("🧵  Filamentos")
        self.btn_nav_fil.setCheckable(True)
        self.btn_nav_fil.setChecked(True)
        self.btn_nav_fil.clicked.connect(lambda: self._switch_module("filamentos"))

        self.btn_nav_imp = QPushButton("🖨️  Impressoras")
        self.btn_nav_imp.setCheckable(True)
        self.btn_nav_imp.setChecked(False)
        self.btn_nav_imp.clicked.connect(lambda: self._switch_module("impressoras"))

        for btn in (self.btn_nav_fil, self.btn_nav_imp):
            btn.setStyleSheet("""
                QPushButton {
                    background: white; color: #5a6070;
                    border: 1px solid #dde1ea; border-radius: 6px;
                    padding: 7px 6px; font-size: 12px; font-weight: 600;
                }
                QPushButton:checked {
                    background: #4F9900; color: white; border-color: #4F9900;
                }
                QPushButton:hover:!checked { background: #f8f8f8; }
            """)
            nav_layout.addWidget(btn)

        layout.addWidget(nav)

        # ── Seção Filamentos ──────────────────────────────────────────
        self.fil_section = QWidget()
        fil_layout = QVBoxLayout(self.fil_section)
        fil_layout.setContentsMargins(0, 0, 0, 0)
        fil_layout.setSpacing(0)

        cat_header = QWidget()
        cat_header.setObjectName("catHeader")
        ch_layout = QHBoxLayout(cat_header)
        ch_layout.setContentsMargins(16, 12, 8, 8)
        cat_title = QLabel("CATEGORIAS")
        cat_title.setObjectName("sectionTitle")
        add_cat_btn = QToolButton()
        add_cat_btn.setText("+")
        add_cat_btn.setObjectName("addCatBtn")
        add_cat_btn.setToolTip("Nova categoria")
        add_cat_btn.clicked.connect(self._add_categoria)
        ch_layout.addWidget(cat_title)
        ch_layout.addStretch()
        ch_layout.addWidget(add_cat_btn)
        fil_layout.addWidget(cat_header)

        self.cat_list = QListWidget()
        self.cat_list.setObjectName("catList")
        self.cat_list.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)
        self.cat_list.setDefaultDropAction(Qt.DropAction.MoveAction)
        self.cat_list.currentItemChanged.connect(self._on_categoria_changed)
        self.cat_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.cat_list.customContextMenuRequested.connect(self._cat_context_menu)
        self.cat_list.model().rowsMoved.connect(self._on_cat_reordered)
        fil_layout.addWidget(self.cat_list, stretch=1)

        sep_fil = QFrame()
        sep_fil.setFrameShape(QFrame.Shape.HLine)
        sep_fil.setObjectName("separator")
        fil_layout.addWidget(sep_fil)

        export_fil = QWidget()
        export_fil.setObjectName("exportWrap")
        efl = QVBoxLayout(export_fil)
        efl.setContentsMargins(16, 12, 16, 16)
        efl.setSpacing(8)
        btn_loja_fil = QPushButton("🏪  Exportar Loja")
        btn_loja_fil.setObjectName("exportBtn")
        btn_loja_fil.clicked.connect(lambda: self._export_pdf(mostrar_sku=True))
        btn_cli_fil = QPushButton("👤  Exportar Cliente")
        btn_cli_fil.setObjectName("exportBtnSecondary")
        btn_cli_fil.clicked.connect(lambda: self._export_pdf(mostrar_sku=False))
        efl.addWidget(btn_loja_fil)
        efl.addWidget(btn_cli_fil)
        fil_layout.addWidget(export_fil)

        layout.addWidget(self.fil_section, stretch=1)

        # ── Seção Impressoras ─────────────────────────────────────────
        self.imp_section = QWidget()
        imp_layout = QVBoxLayout(self.imp_section)
        imp_layout.setContentsMargins(0, 0, 0, 0)
        imp_layout.setSpacing(0)

        imp_cat_header = QWidget()
        imp_cat_header.setObjectName("catHeader")
        ich_layout = QHBoxLayout(imp_cat_header)
        ich_layout.setContentsMargins(16, 12, 8, 8)
        imp_cat_title = QLabel("CATEGORIAS")
        imp_cat_title.setObjectName("sectionTitle")
        add_imp_cat_btn = QToolButton()
        add_imp_cat_btn.setText("+")
        add_imp_cat_btn.setObjectName("addCatBtn")
        add_imp_cat_btn.setToolTip("Nova categoria")
        add_imp_cat_btn.clicked.connect(self._imp_add_categoria)
        ich_layout.addWidget(imp_cat_title)
        ich_layout.addStretch()
        ich_layout.addWidget(add_imp_cat_btn)
        imp_layout.addWidget(imp_cat_header)

        self.imp_cat_list = QListWidget()
        self.imp_cat_list.setObjectName("catList")
        self.imp_cat_list.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)
        self.imp_cat_list.setDefaultDropAction(Qt.DropAction.MoveAction)
        self.imp_cat_list.currentItemChanged.connect(self._imp_on_categoria_changed)
        self.imp_cat_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.imp_cat_list.customContextMenuRequested.connect(self._imp_cat_context_menu)
        self.imp_cat_list.model().rowsMoved.connect(self._on_imp_cat_reordered)
        imp_layout.addWidget(self.imp_cat_list, stretch=1)

        sep_imp = QFrame()
        sep_imp.setFrameShape(QFrame.Shape.HLine)
        sep_imp.setObjectName("separator")
        imp_layout.addWidget(sep_imp)

        export_imp = QWidget()
        export_imp.setObjectName("exportWrap")
        eil = QVBoxLayout(export_imp)
        eil.setContentsMargins(16, 12, 16, 16)
        eil.setSpacing(8)
        btn_loja_imp = QPushButton("🏪  Exportar Loja")
        btn_loja_imp.setObjectName("exportBtn")
        btn_loja_imp.clicked.connect(lambda: self._imp_export_pdf(mostrar_sku=True))
        btn_cli_imp = QPushButton("👤  Exportar Cliente")
        btn_cli_imp.setObjectName("exportBtnSecondary")
        btn_cli_imp.clicked.connect(lambda: self._imp_export_pdf(mostrar_sku=False))
        eil.addWidget(btn_loja_imp)
        eil.addWidget(btn_cli_imp)
        imp_layout.addWidget(export_imp)

        layout.addWidget(self.imp_section, stretch=1)
        self.imp_section.hide()

        return sidebar

    def _switch_module(self, module):
        if module == "filamentos":
            self.content_stack.setCurrentIndex(0)
            self.fil_section.show()
            self.imp_section.hide()
            self.btn_nav_fil.setChecked(True)
            self.btn_nav_imp.setChecked(False)
        else:
            self.content_stack.setCurrentIndex(1)
            self.fil_section.hide()
            self.imp_section.show()
            self.btn_nav_fil.setChecked(False)
            self.btn_nav_imp.setChecked(True)
            if self.imp_cat_list.count() == 0:
                self._imp_load_categorias()

    # ═══════════════════════════════════════════════════════════════════
    # CONTEÚDO FILAMENTOS
    # ═══════════════════════════════════════════════════════════════════

    def _build_filamentos_content(self):
        content = QFrame()
        content.setObjectName("contentArea")
        self.content_layout = QVBoxLayout(content)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.setSpacing(0)

        self.topbar_widget = QWidget()
        self.topbar_widget.setObjectName("topbar")
        tb_layout = QHBoxLayout(self.topbar_widget)
        tb_layout.setContentsMargins(28, 16, 24, 16)
        tb_layout.setSpacing(12)

        self.page_title = QLabel("Todos os Filamentos")
        self.page_title.setObjectName("pageTitle")
        tb_layout.addWidget(self.page_title)
        tb_layout.addStretch()

        self.search_input = QLineEdit()
        self.search_input.setObjectName("searchInput")
        self.search_input.setPlaceholderText("🔍  Buscar por cor ou categoria...")
        self.search_input.setFixedWidth(280)
        self.search_input.textChanged.connect(self._on_search)
        self.search_input.setClearButtonEnabled(True)
        tb_layout.addWidget(self.search_input)

        self.count_label = QLabel("")
        self.count_label.setObjectName("countLabel")
        tb_layout.addWidget(self.count_label)

        self.select_mode_btn = QPushButton("☑  Selecionar")
        self.select_mode_btn.setObjectName("addFilBtn")
        self.select_mode_btn.clicked.connect(self._enter_selection_mode)
        tb_layout.addWidget(self.select_mode_btn)

        add_fil_btn = QPushButton("+ Novo Filamento")
        add_fil_btn.setObjectName("addFilBtn")
        add_fil_btn.clicked.connect(self._add_filamento)
        tb_layout.addWidget(add_fil_btn)

        self.content_layout.addWidget(self.topbar_widget)
        self.topbar_widget.hide()

        self.list_header = QWidget()
        self.list_header.setObjectName("listHeader")
        hh = QHBoxLayout(self.list_header)
        hh.setContentsMargins(SIDE_MARGIN + 10, 6, SIDE_MARGIN + 10, 6)
        hh.setSpacing(0)

        def hcol(text, width, align=Qt.AlignmentFlag.AlignCenter):
            lbl = QLabel(text)
            lbl.setObjectName("listHeaderLabel")
            lbl.setFixedWidth(width)
            lbl.setAlignment(align | Qt.AlignmentFlag.AlignVCenter)
            return lbl

        hh.addWidget(hcol("ESTOQUE", COL_ESTOQUE))
        hh.addWidget(hcol("SKU", COL_SKU))
        hh.addWidget(hcol("CÓDIGO", COL_CODIGO))
        hh.addWidget(hcol("", COL_IMG))
        hh.addWidget(hcol("COR", COL_COR))
        hh.addWidget(hcol("PREÇO", COL_PRECO))
        hh.addWidget(hcol("QTD", COL_QTD))
        hh.addStretch()
        self.content_layout.addWidget(self.list_header)
        self.list_header.hide()

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setObjectName("scrollArea")
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.cards_container = QWidget()
        self.cards_container.setObjectName("cardsContainer")
        self.cards_layout = QVBoxLayout(self.cards_container)
        self.cards_layout.setContentsMargins(SIDE_MARGIN, 8, SIDE_MARGIN, 16)
        self.cards_layout.setSpacing(4)
        self.cards_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.scroll.setWidget(self.cards_container)
        self.content_layout.addWidget(self.scroll, stretch=1)
        self.scroll.hide()

        self.placeholder = QLabel("")
        self.placeholder.setObjectName("placeholder")
        self.placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.content_layout.addWidget(self.placeholder, stretch=1)
        self.placeholder.hide()

        self.selection_bar = QWidget()
        self.selection_bar.setStyleSheet("background-color: #4F9900;")
        sb_layout = QHBoxLayout(self.selection_bar)
        sb_layout.setContentsMargins(24, 10, 24, 10)
        sb_layout.setSpacing(12)
        self.selection_count_label = QLabel("0 selecionados")
        self.selection_count_label.setStyleSheet("color: white; font-weight: 700; font-size: 13px;")
        sb_layout.addWidget(self.selection_count_label)
        sb_layout.addStretch()
        self.edit_values_btn = QPushButton("✎  Alterar Valores")
        self.edit_values_btn.setStyleSheet("background: white; color: #4F9900; font-weight: 700; border-radius: 6px; padding: 7px 18px;")
        self.edit_values_btn.setEnabled(False)
        self.edit_values_btn.clicked.connect(self._edit_selected_values)
        sb_layout.addWidget(self.edit_values_btn)
        self.duplicate_btn = QPushButton("⧉  Duplicar")
        self.duplicate_btn.setStyleSheet("background: white; color: #4F9900; font-weight: 700; border-radius: 6px; padding: 7px 18px;")
        self.duplicate_btn.setEnabled(False)
        self.duplicate_btn.clicked.connect(self._duplicate_selected)
        sb_layout.addWidget(self.duplicate_btn)
        self.delete_selected_btn = QPushButton("🗑  Apagar")
        self.delete_selected_btn.setStyleSheet("background: #e02d2d; color: white; font-weight: 700; border-radius: 6px; padding: 7px 18px;")
        self.delete_selected_btn.setEnabled(False)
        self.delete_selected_btn.clicked.connect(self._delete_selected)
        sb_layout.addWidget(self.delete_selected_btn)
        cancel_sel_btn = QPushButton("Cancelar")
        cancel_sel_btn.setStyleSheet("background: transparent; color: white; border: 1px solid rgba(255,255,255,0.5); border-radius: 6px; padding: 7px 18px;")
        cancel_sel_btn.clicked.connect(self._exit_selection_mode)
        sb_layout.addWidget(cancel_sel_btn)
        self.content_layout.addWidget(self.selection_bar)
        self.selection_bar.hide()

        return content

    # ═══════════════════════════════════════════════════════════════════
    # CONTEÚDO IMPRESSORAS
    # ═══════════════════════════════════════════════════════════════════

    def _build_impressoras_content(self):
        content = QFrame()
        content.setObjectName("contentArea")
        self.imp_content_layout = QVBoxLayout(content)
        self.imp_content_layout.setContentsMargins(0, 0, 0, 0)
        self.imp_content_layout.setSpacing(0)

        self.imp_topbar = QWidget()
        self.imp_topbar.setObjectName("topbar")
        tb = QHBoxLayout(self.imp_topbar)
        tb.setContentsMargins(28, 16, 24, 16)
        tb.setSpacing(12)

        self.imp_page_title = QLabel("Todas as Impressoras")
        self.imp_page_title.setObjectName("pageTitle")
        tb.addWidget(self.imp_page_title)
        tb.addStretch()

        self.imp_search_input = QLineEdit()
        self.imp_search_input.setObjectName("searchInput")
        self.imp_search_input.setPlaceholderText("🔍  Buscar por modelo ou categoria...")
        self.imp_search_input.setFixedWidth(280)
        self.imp_search_input.textChanged.connect(self._imp_on_search)
        self.imp_search_input.setClearButtonEnabled(True)
        tb.addWidget(self.imp_search_input)

        self.imp_count_label = QLabel("")
        self.imp_count_label.setObjectName("countLabel")
        tb.addWidget(self.imp_count_label)

        self.imp_select_mode_btn = QPushButton("☑  Selecionar")
        self.imp_select_mode_btn.setObjectName("addFilBtn")
        self.imp_select_mode_btn.clicked.connect(self._imp_enter_selection_mode)
        tb.addWidget(self.imp_select_mode_btn)

        add_imp_btn = QPushButton("+ Nova Impressora")
        add_imp_btn.setObjectName("addFilBtn")
        add_imp_btn.clicked.connect(self._imp_add)
        tb.addWidget(add_imp_btn)

        self.imp_content_layout.addWidget(self.imp_topbar)
        self.imp_topbar.hide()

        self.imp_list_header = QWidget()
        self.imp_list_header.setObjectName("listHeader")
        hh = QHBoxLayout(self.imp_list_header)
        hh.setContentsMargins(SIDE_MARGIN + 10, 6, SIDE_MARGIN + 10, 6)
        hh.setSpacing(0)

        def hcol(text, width):
            lbl = QLabel(text)
            lbl.setObjectName("listHeaderLabel")
            lbl.setFixedWidth(width)
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
            return lbl

        from ui.impressora_card import COL_ESTOQUE as IE, COL_SKU as IS, COL_CODIGO as IC, COL_IMG as II, COL_MODELO as IM, COL_PRECO_AVISTA as IA, COL_PRECO as IP, COL_QTD as IQ
        hh.addWidget(hcol("ESTOQUE", IE))
        hh.addWidget(hcol("SKU", IS))
        hh.addWidget(hcol("CÓDIGO", IC))
        hh.addWidget(hcol("", II))
        hh.addWidget(hcol("MODELO", IM))
        hh.addWidget(hcol("À VISTA", IA))
        hh.addWidget(hcol("10x S/JUROS", IP))
        hh.addWidget(hcol("QTD", IQ))
        hh.addStretch()
        self.imp_content_layout.addWidget(self.imp_list_header)
        self.imp_list_header.hide()

        self.imp_scroll = QScrollArea()
        self.imp_scroll.setWidgetResizable(True)
        self.imp_scroll.setObjectName("scrollArea")
        self.imp_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.imp_cards_container = QWidget()
        self.imp_cards_container.setObjectName("cardsContainer")
        self.imp_cards_layout = QVBoxLayout(self.imp_cards_container)
        self.imp_cards_layout.setContentsMargins(SIDE_MARGIN, 8, SIDE_MARGIN, 16)
        self.imp_cards_layout.setSpacing(4)
        self.imp_cards_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.imp_scroll.setWidget(self.imp_cards_container)
        self.imp_content_layout.addWidget(self.imp_scroll, stretch=1)
        self.imp_scroll.hide()

        self.imp_placeholder = QLabel("")
        self.imp_placeholder.setObjectName("placeholder")
        self.imp_placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.imp_content_layout.addWidget(self.imp_placeholder, stretch=1)
        self.imp_placeholder.hide()

        self.imp_selection_bar = QWidget()
        self.imp_selection_bar.setStyleSheet("background-color: #4F9900;")
        isb = QHBoxLayout(self.imp_selection_bar)
        isb.setContentsMargins(24, 10, 24, 10)
        isb.setSpacing(12)
        self.imp_selection_count_label = QLabel("0 selecionados")
        self.imp_selection_count_label.setStyleSheet("color: white; font-weight: 700; font-size: 13px;")
        isb.addWidget(self.imp_selection_count_label)
        isb.addStretch()
        self.imp_edit_values_btn = QPushButton("✎  Alterar Valores")
        self.imp_edit_values_btn.setStyleSheet("background: white; color: #4F9900; font-weight: 700; border-radius: 6px; padding: 7px 18px;")
        self.imp_edit_values_btn.setEnabled(False)
        self.imp_edit_values_btn.clicked.connect(self._imp_edit_selected_values)
        isb.addWidget(self.imp_edit_values_btn)
        self.imp_duplicate_btn = QPushButton("⧉  Duplicar")
        self.imp_duplicate_btn.setStyleSheet("background: white; color: #4F9900; font-weight: 700; border-radius: 6px; padding: 7px 18px;")
        self.imp_duplicate_btn.setEnabled(False)
        self.imp_duplicate_btn.clicked.connect(self._imp_duplicate_selected)
        isb.addWidget(self.imp_duplicate_btn)
        self.imp_delete_btn = QPushButton("🗑  Apagar")
        self.imp_delete_btn.setStyleSheet("background: #e02d2d; color: white; font-weight: 700; border-radius: 6px; padding: 7px 18px;")
        self.imp_delete_btn.setEnabled(False)
        self.imp_delete_btn.clicked.connect(self._imp_delete_selected)
        isb.addWidget(self.imp_delete_btn)
        imp_cancel_btn = QPushButton("Cancelar")
        imp_cancel_btn.setStyleSheet("background: transparent; color: white; border: 1px solid rgba(255,255,255,0.5); border-radius: 6px; padding: 7px 18px;")
        imp_cancel_btn.clicked.connect(self._imp_exit_selection_mode)
        isb.addWidget(imp_cancel_btn)
        self.imp_content_layout.addWidget(self.imp_selection_bar)
        self.imp_selection_bar.hide()

        return content

    # ═══════════════════════════════════════════════════════════════════
    # FILAMENTOS — helpers de visibilidade
    # ═══════════════════════════════════════════════════════════════════

    def _show_lista(self):
        self.topbar_widget.show()
        self.list_header.show()
        self.scroll.show()
        self.placeholder.hide()

    def _show_placeholder(self, texto, mostrar_topbar=False):
        self.topbar_widget.setVisible(mostrar_topbar)
        self.list_header.hide()
        self.scroll.hide()
        self.placeholder.setText(texto)
        self.placeholder.show()

    # ═══════════════════════════════════════════════════════════════════
    # FILAMENTOS — busca
    # ═══════════════════════════════════════════════════════════════════

    def _on_search(self, texto):
        self._search_pending_text = texto
        self._search_timer.start()

    def _do_search(self):
        texto = self._search_pending_text.strip().lower()
        if not texto:
            self._render_filamentos(self._todos_filamentos)
            return
        filtrados = [
            f for f in self._todos_filamentos
            if texto in f.get("nome", "").lower()
            or texto in f.get("categoria_nome", "").lower()
            or texto in f.get("marca", "").lower()
        ]
        self._render_filamentos(filtrados, busca=texto)

    # ═══════════════════════════════════════════════════════════════════
    # FILAMENTOS — categorias
    # ═══════════════════════════════════════════════════════════════════

    def _load_categorias(self):
        self.cat_list.clear()
        all_item = QListWidgetItem("📦  Todos os Filamentos")
        all_item.setData(Qt.ItemDataRole.UserRole, None)
        all_item.setFlags(all_item.flags() & ~Qt.ItemFlag.ItemIsDragEnabled)
        self.cat_list.addItem(all_item)
        for cat in self.db.get_categorias():
            item = QListWidgetItem(f"  {cat['nome']}")
            item.setData(Qt.ItemDataRole.UserRole, cat["id"])
            self.cat_list.addItem(item)
        self.cat_list.setCurrentRow(0)

    def _on_cat_reordered(self, *_):
        ids = [
            self.cat_list.item(i).data(Qt.ItemDataRole.UserRole)
            for i in range(1, self.cat_list.count())
        ]
        self.db.reorder_categorias(ids)

    def _on_categoria_changed(self, current, previous):
        if current is None:
            return
        self.current_categoria_id = current.data(Qt.ItemDataRole.UserRole)
        self.page_title.setText(current.text().strip() or "Todos os Filamentos")
        self.search_input.clear()
        self._load_filamentos()

    def _add_categoria(self):
        if CategoriaDialog(self, self.db).exec():
            self._load_categorias()
            self.status_bar.showMessage("Categoria adicionada com sucesso!")

    def _cat_context_menu(self, pos):
        item = self.cat_list.itemAt(pos)
        if item is None:
            return
        cat_id = item.data(Qt.ItemDataRole.UserRole)
        if cat_id is None:
            return
        menu = QMenu(self)
        menu.setStyleSheet("QMenu { background: #ffffff; color: #1a1f36; border: 1px solid #dde1ea; } QMenu::item:selected { background: #e8f0fd; color: #4F9900; }")
        edit_act = menu.addAction("✏  Renomear")
        del_act  = menu.addAction("🗑  Excluir")
        action = menu.exec(self.cat_list.mapToGlobal(pos))
        if action == edit_act:
            if CategoriaDialog(self, self.db, item.text().strip(), cat_id).exec():
                self._load_categorias()
        elif action == del_act:
            ok, msg = self.db.delete_categoria(cat_id)
            if ok:
                self._load_categorias()
                self.status_bar.showMessage(msg)
            else:
                QMessageBox.warning(self, "Não foi possível excluir", msg)

    # ═══════════════════════════════════════════════════════════════════
    # FILAMENTOS — CRUD
    # ═══════════════════════════════════════════════════════════════════

    def _load_filamentos(self):
        self._todos_filamentos = self.db.get_filamentos(categoria_id=self.current_categoria_id)
        self._render_filamentos(self._todos_filamentos)

    def _render_filamentos(self, filamentos, busca=""):
        self._pending_render = []
        self._card_refs = []
        if self._selection_mode:
            self._selected_ids.clear()
            self._update_selection_bar()

        while self.cards_layout.count():
            w = self.cards_layout.takeAt(0)
            if w.widget():
                w.widget().deleteLater()

        if not filamentos:
            self._show_placeholder(
                f'Nenhum resultado para "{busca}".' if busca
                else "Nenhum filamento cadastrado nesta categoria.\nClique em '+ Novo Filamento' para começar.",
                mostrar_topbar=True
            )
            self.count_label.setText("")
            return

        total = len(filamentos)
        sufixo = f" encontrado{'s' if total > 1 else ''}" if busca else ""
        self.count_label.setText(f"{total} filamento{'s' if total > 1 else ''}{sufixo}")
        self._show_lista()
        self._pending_render = list(filamentos)
        self._render_next_batch()

    def _render_next_batch(self):
        if not self._pending_render:
            return
        for fil in self._pending_render[:30]:
            card = FilamentoCard(fil, self.db, self._pixmap_cache)
            card.edit_requested.connect(self._edit_filamento)
            card.delete_requested.connect(self._delete_filamento)
            card.selection_toggled.connect(self._on_card_selection_changed)
            if self._selection_mode:
                card.set_selection_mode(True)
            self._card_refs.append(card)
            self.cards_layout.addWidget(card)
        self._pending_render = self._pending_render[30:]
        if self._pending_render:
            QTimer.singleShot(0, self._render_next_batch)

    def _add_filamento(self):
        cat_id = self.current_categoria_id
        if FilamentoDialog(self, self.db, categoria_id=cat_id).exec():
            self._load_filamentos()
            self.status_bar.showMessage("Filamento adicionado com sucesso!")

    def _edit_filamento(self, filamento_id):
        if FilamentoDialog(self, self.db, filamento_id=filamento_id).exec():
            self._load_filamentos()
            self.status_bar.showMessage("Filamento atualizado!")

    def _delete_filamento(self, filamento_id):
        reply = QMessageBox.question(self, "Confirmar exclusão", "Deseja remover este filamento?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            self.db.delete_filamento(filamento_id)
            self._load_filamentos()
            self.status_bar.showMessage("Filamento removido.")

    # ── Seleção filamentos ────────────────────────────────────────────

    def _enter_selection_mode(self):
        self._selection_mode = True
        self._selected_ids.clear()
        for card in self._card_refs:
            card.set_selection_mode(True)
        self.select_mode_btn.setText("✕  Cancelar seleção")
        self.select_mode_btn.clicked.disconnect()
        self.select_mode_btn.clicked.connect(self._exit_selection_mode)
        self.selection_bar.hide()

    def _exit_selection_mode(self):
        self._selection_mode = False
        self._selected_ids.clear()
        for card in self._card_refs:
            card.set_selection_mode(False)
        self.select_mode_btn.setText("☑  Selecionar")
        self.select_mode_btn.clicked.disconnect()
        self.select_mode_btn.clicked.connect(self._enter_selection_mode)
        self.selection_bar.hide()

    def _on_card_selection_changed(self, fil_id, selected):
        if selected:
            self._selected_ids.add(fil_id)
        else:
            self._selected_ids.discard(fil_id)
        self._update_selection_bar()

    def _update_selection_bar(self):
        n = len(self._selected_ids)
        self.selection_count_label.setText(f"{n} filamento{'s' if n != 1 else ''} selecionado{'s' if n != 1 else ''}")
        self.edit_values_btn.setEnabled(n > 0)
        self.duplicate_btn.setEnabled(n > 0)
        self.delete_selected_btn.setEnabled(n > 0)
        self.selection_bar.show() if n > 0 else self.selection_bar.hide()

    def _edit_selected_values(self):
        if not self._selected_ids:
            return
        ids = list(self._selected_ids)
        dialog = AlterarValoresDialog(self, len(ids), self.db.get_categorias)
        if not dialog.exec():
            return
        campos = dialog.get_values()
        if not campos:
            return
        # filamentos armazenam preço em peso_total
        if "preco" in campos:
            campos["peso_total"] = campos.pop("preco")
        self.db.bulk_patch_filamentos(ids, campos)
        self._exit_selection_mode()
        self._load_filamentos()
        self.status_bar.showMessage(f"{len(ids)} filamento{'s' if len(ids) != 1 else ''} atualizado{'s' if len(ids) != 1 else ''}!")

    def _delete_selected(self):
        if not self._selected_ids:
            return
        n = len(self._selected_ids)
        reply = QMessageBox.question(self, "Confirmar exclusão",
            f"Deseja remover {n} filamento{'s' if n != 1 else ''} selecionado{'s' if n != 1 else ''}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply != QMessageBox.StandardButton.Yes:
            return
        for fil_id in list(self._selected_ids):
            self.db.delete_filamento(fil_id)
        self._exit_selection_mode()
        self._load_filamentos()
        self.status_bar.showMessage(f"{n} filamento{'s' if n != 1 else ''} removido{'s' if n != 1 else ''}.")

    def _duplicate_selected(self):
        if not self._selected_ids:
            return
        ids = list(self._selected_ids)
        dialog = DuplicarDialog(self, self.db, len(ids))
        if not dialog.exec():
            return
        cat_id, preco = dialog.get_values()
        for fil_id in ids:
            self.db.duplicate_filamento(fil_id, categoria_id=cat_id, preco=preco)
        n = len(ids)
        self._exit_selection_mode()
        self._load_filamentos()
        self.status_bar.showMessage(f"{n} filamento{'s' if n != 1 else ''} duplicado{'s' if n != 1 else ''}!")

    # ── PDF filamentos ────────────────────────────────────────────────

    def _export_pdf(self, mostrar_sku: bool):
        tipo = "Loja" if mostrar_sku else "Cliente"
        try:
            tmp = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False)
            temp_path = tmp.name
            tmp.close()
            PDFExporter(self.db).export(temp_path, mostrar_sku=mostrar_sku)
        except Exception as e:
            QMessageBox.critical(self, "Erro ao gerar PDF", f"Não foi possível gerar o PDF:\n\n{e}")
            return
        if platform.system() == "Darwin":
            subprocess.run(["open", temp_path])
        elif platform.system() == "Windows":
            os.startfile(temp_path)
        else:
            subprocess.run(["xdg-open", temp_path])
        reply = QMessageBox.question(self, "Salvar PDF",
            f"O PDF {tipo} foi aberto no visualizador.\n\nDeseja salvar uma cópia?",
            QMessageBox.StandardButton.Save | QMessageBox.StandardButton.Discard,
            QMessageBox.StandardButton.Save)
        if reply == QMessageBox.StandardButton.Save:
            path, _ = QFileDialog.getSaveFileName(self, "Salvar PDF", f"LaBlu_Filamentos_{tipo}.pdf", "PDF (*.pdf)")
            if path:
                shutil.copy2(temp_path, path)
                self.status_bar.showMessage(f"PDF {tipo} salvo: {path}")
                QMessageBox.information(self, "Sucesso!", f"PDF salvo em:\n{path}")
        QTimer.singleShot(30000, lambda: os.unlink(temp_path) if os.path.exists(temp_path) else None)

    # ═══════════════════════════════════════════════════════════════════
    # IMPRESSORAS — helpers de visibilidade
    # ═══════════════════════════════════════════════════════════════════

    def _imp_show_lista(self):
        self.imp_topbar.show()
        self.imp_list_header.show()
        self.imp_scroll.show()
        self.imp_placeholder.hide()

    def _imp_show_placeholder(self, texto, mostrar_topbar=False):
        self.imp_topbar.setVisible(mostrar_topbar)
        self.imp_list_header.hide()
        self.imp_scroll.hide()
        self.imp_placeholder.setText(texto)
        self.imp_placeholder.show()

    # ═══════════════════════════════════════════════════════════════════
    # IMPRESSORAS — busca
    # ═══════════════════════════════════════════════════════════════════

    def _imp_on_search(self, texto):
        self._imp_search_pending = texto
        self._imp_search_timer.start()

    def _imp_do_search(self):
        texto = self._imp_search_pending.strip().lower()
        if not texto:
            self._imp_render(self._imp_todos)
            return
        filtrados = [
            i for i in self._imp_todos
            if texto in i.get("modelo", "").lower()
            or texto in i.get("categoria_nome", "").lower()
            or texto in i.get("marca", "").lower()
        ]
        self._imp_render(filtrados, busca=texto)

    # ═══════════════════════════════════════════════════════════════════
    # IMPRESSORAS — categorias
    # ═══════════════════════════════════════════════════════════════════

    def _imp_load_categorias(self):
        self.imp_cat_list.clear()
        all_item = QListWidgetItem("🖨️  Todas as Impressoras")
        all_item.setData(Qt.ItemDataRole.UserRole, None)
        all_item.setFlags(all_item.flags() & ~Qt.ItemFlag.ItemIsDragEnabled)
        self.imp_cat_list.addItem(all_item)
        for cat in self.db.get_categorias_impressoras():
            item = QListWidgetItem(f"  {cat['nome']}")
            item.setData(Qt.ItemDataRole.UserRole, cat["id"])
            self.imp_cat_list.addItem(item)
        self.imp_cat_list.setCurrentRow(0)

    def _on_imp_cat_reordered(self, *_):
        ids = [
            self.imp_cat_list.item(i).data(Qt.ItemDataRole.UserRole)
            for i in range(1, self.imp_cat_list.count())
        ]
        self.db.reorder_categorias_impressoras(ids)

    def _imp_on_categoria_changed(self, current, previous):
        if current is None:
            return
        self._imp_categoria_id = current.data(Qt.ItemDataRole.UserRole)
        self.imp_page_title.setText(current.text().strip() or "Todas as Impressoras")
        self.imp_search_input.clear()
        self._imp_load()

    def _imp_add_categoria(self):
        dialog = CategoriaDialog(self, self.db,
            add_fn=self.db.add_categoria_impressora,
            update_fn=None)
        if dialog.exec():
            self._imp_load_categorias()
            self.status_bar.showMessage("Categoria adicionada com sucesso!")

    def _imp_cat_context_menu(self, pos):
        item = self.imp_cat_list.itemAt(pos)
        if item is None:
            return
        cat_id = item.data(Qt.ItemDataRole.UserRole)
        if cat_id is None:
            return
        menu = QMenu(self)
        menu.setStyleSheet("QMenu { background: #ffffff; color: #1a1f36; border: 1px solid #dde1ea; } QMenu::item:selected { background: #e8f0fd; color: #4F9900; }")
        edit_act = menu.addAction("✏  Renomear")
        del_act  = menu.addAction("🗑  Excluir")
        action = menu.exec(self.imp_cat_list.mapToGlobal(pos))
        if action == edit_act:
            dialog = CategoriaDialog(self, self.db, item.text().strip(), cat_id,
                update_fn=self.db.update_categoria_impressora)
            if dialog.exec():
                self._imp_load_categorias()
        elif action == del_act:
            ok, msg = self.db.delete_categoria_impressora(cat_id)
            if ok:
                self._imp_load_categorias()
                self.status_bar.showMessage(msg)
            else:
                QMessageBox.warning(self, "Não foi possível excluir", msg)

    # ═══════════════════════════════════════════════════════════════════
    # IMPRESSORAS — CRUD
    # ═══════════════════════════════════════════════════════════════════

    def _imp_load(self):
        self._imp_todos = self.db.get_impressoras(categoria_id=self._imp_categoria_id)
        self._imp_render(self._imp_todos)

    def _imp_render(self, impressoras, busca=""):
        self._imp_pending_render = []
        self._imp_card_refs = []
        if self._imp_selection_mode:
            self._imp_selected_ids.clear()
            self._imp_update_selection_bar()

        while self.imp_cards_layout.count():
            w = self.imp_cards_layout.takeAt(0)
            if w.widget():
                w.widget().deleteLater()

        if not impressoras:
            self._imp_show_placeholder(
                f'Nenhum resultado para "{busca}".' if busca
                else "Nenhuma impressora cadastrada nesta categoria.\nClique em '+ Nova Impressora' para começar.",
                mostrar_topbar=True
            )
            self.imp_count_label.setText("")
            return

        total = len(impressoras)
        sufixo = f" encontrada{'s' if total > 1 else ''}" if busca else ""
        self.imp_count_label.setText(f"{total} impressora{'s' if total > 1 else ''}{sufixo}")
        self._imp_show_lista()
        self._imp_pending_render = list(impressoras)
        self._imp_render_next_batch()

    def _imp_render_next_batch(self):
        if not self._imp_pending_render:
            return
        for imp in self._imp_pending_render[:30]:
            card = ImpressoraCard(imp, self.db, self._pixmap_cache)
            card.edit_requested.connect(self._imp_edit)
            card.delete_requested.connect(self._imp_delete)
            card.selection_toggled.connect(self._imp_on_card_selection_changed)
            if self._imp_selection_mode:
                card.set_selection_mode(True)
            self._imp_card_refs.append(card)
            self.imp_cards_layout.addWidget(card)
        self._imp_pending_render = self._imp_pending_render[30:]
        if self._imp_pending_render:
            QTimer.singleShot(0, self._imp_render_next_batch)

    def _imp_add(self):
        if ImpressoraDialog(self, self.db, categoria_id=self._imp_categoria_id).exec():
            self._imp_load()
            self.status_bar.showMessage("Impressora adicionada com sucesso!")

    def _imp_edit(self, impressora_id):
        if ImpressoraDialog(self, self.db, impressora_id=impressora_id).exec():
            self._imp_load()
            self.status_bar.showMessage("Impressora atualizada!")

    def _imp_delete(self, impressora_id):
        reply = QMessageBox.question(self, "Confirmar exclusão", "Deseja remover esta impressora?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            self.db.delete_impressora(impressora_id)
            self._imp_load()
            self.status_bar.showMessage("Impressora removida.")

    # ── Seleção impressoras ───────────────────────────────────────────

    def _imp_enter_selection_mode(self):
        self._imp_selection_mode = True
        self._imp_selected_ids.clear()
        for card in self._imp_card_refs:
            card.set_selection_mode(True)
        self.imp_select_mode_btn.setText("✕  Cancelar seleção")
        self.imp_select_mode_btn.clicked.disconnect()
        self.imp_select_mode_btn.clicked.connect(self._imp_exit_selection_mode)
        self.imp_selection_bar.hide()

    def _imp_exit_selection_mode(self):
        self._imp_selection_mode = False
        self._imp_selected_ids.clear()
        for card in self._imp_card_refs:
            card.set_selection_mode(False)
        self.imp_select_mode_btn.setText("☑  Selecionar")
        self.imp_select_mode_btn.clicked.disconnect()
        self.imp_select_mode_btn.clicked.connect(self._imp_enter_selection_mode)
        self.imp_selection_bar.hide()

    def _imp_on_card_selection_changed(self, imp_id, selected):
        if selected:
            self._imp_selected_ids.add(imp_id)
        else:
            self._imp_selected_ids.discard(imp_id)
        self._imp_update_selection_bar()

    def _imp_update_selection_bar(self):
        n = len(self._imp_selected_ids)
        self.imp_selection_count_label.setText(f"{n} impressora{'s' if n != 1 else ''} selecionada{'s' if n != 1 else ''}")
        self.imp_edit_values_btn.setEnabled(n > 0)
        self.imp_duplicate_btn.setEnabled(n > 0)
        self.imp_delete_btn.setEnabled(n > 0)
        self.imp_selection_bar.show() if n > 0 else self.imp_selection_bar.hide()

    def _imp_edit_selected_values(self):
        if not self._imp_selected_ids:
            return
        ids = list(self._imp_selected_ids)
        dialog = AlterarValoresDialog(self, len(ids),
                                      self.db.get_categorias_impressoras,
                                      item_label="impressora")
        if not dialog.exec():
            return
        campos = dialog.get_values()
        if not campos:
            return
        self.db.bulk_patch_impressoras(ids, campos)
        self._imp_exit_selection_mode()
        self._imp_load()
        self.status_bar.showMessage(f"{len(ids)} impressora{'s' if len(ids) != 1 else ''} atualizada{'s' if len(ids) != 1 else ''}!")

    def _imp_delete_selected(self):
        if not self._imp_selected_ids:
            return
        n = len(self._imp_selected_ids)
        reply = QMessageBox.question(self, "Confirmar exclusão",
            f"Deseja remover {n} impressora{'s' if n != 1 else ''} selecionada{'s' if n != 1 else ''}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply != QMessageBox.StandardButton.Yes:
            return
        for imp_id in list(self._imp_selected_ids):
            self.db.delete_impressora(imp_id)
        self._imp_exit_selection_mode()
        self._imp_load()
        self.status_bar.showMessage(f"{n} impressora{'s' if n != 1 else ''} removida{'s' if n != 1 else ''}.")

    def _imp_duplicate_selected(self):
        if not self._imp_selected_ids:
            return
        ids = list(self._imp_selected_ids)
        dialog = DuplicarDialog(self, self.db, len(ids),
                                get_categorias_fn=self.db.get_categorias_impressoras,
                                item_label="impressora")
        if not dialog.exec():
            return
        cat_id, preco = dialog.get_values()
        for imp_id in ids:
            self.db.duplicate_impressora(imp_id, categoria_id=cat_id, preco=preco)
        n = len(ids)
        self._imp_exit_selection_mode()
        self._imp_load()
        self.status_bar.showMessage(f"{n} impressora{'s' if n != 1 else ''} duplicada{'s' if n != 1 else ''}!")

    # ── PDF impressoras ───────────────────────────────────────────────

    def _imp_export_pdf(self, mostrar_sku: bool):
        tipo = "Loja" if mostrar_sku else "Cliente"
        try:
            tmp = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False)
            temp_path = tmp.name
            tmp.close()
            PDFExporterImpressoras(self.db).export(temp_path, mostrar_sku=mostrar_sku)
        except Exception as e:
            QMessageBox.critical(self, "Erro ao gerar PDF", f"Não foi possível gerar o PDF:\n\n{e}")
            return
        if platform.system() == "Darwin":
            subprocess.run(["open", temp_path])
        elif platform.system() == "Windows":
            os.startfile(temp_path)
        else:
            subprocess.run(["xdg-open", temp_path])
        reply = QMessageBox.question(self, "Salvar PDF",
            f"O PDF {tipo} foi aberto no visualizador.\n\nDeseja salvar uma cópia?",
            QMessageBox.StandardButton.Save | QMessageBox.StandardButton.Discard,
            QMessageBox.StandardButton.Save)
        if reply == QMessageBox.StandardButton.Save:
            path, _ = QFileDialog.getSaveFileName(self, "Salvar PDF", f"LaBlu_Impressoras_{tipo}.pdf", "PDF (*.pdf)")
            if path:
                shutil.copy2(temp_path, path)
                self.status_bar.showMessage(f"PDF {tipo} salvo: {path}")
                QMessageBox.information(self, "Sucesso!", f"PDF salvo em:\n{path}")
        QTimer.singleShot(30000, lambda: os.unlink(temp_path) if os.path.exists(temp_path) else None)
