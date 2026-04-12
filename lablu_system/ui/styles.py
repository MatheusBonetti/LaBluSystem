"""
Estilos visuais do LaBlu System.
Tema: Claro / Light — profissional e limpo.
"""

COLORS = {
    "bg_main":       "#f0f2f7",
    "bg_sidebar":    "#ffffff",
    "bg_card":       "#ffffff",
    "bg_topbar":     "#ffffff",
    "bg_header":     "#4F9900",
    "accent":        "#4F9900",
    "accent_hover":  "#4F9900",
    "accent_dark":   "#315F00",
    "accent_light":  "#e8f0fd",
    "text_primary":  "#1a1f36",
    "text_secondary":"#5a6070",
    "text_muted":    "#9aa0b0",
    "border":        "#dde1ea",
    "border_light":  "#eef0f5",
    "success":       "#18a558",
    "danger":        "#e02d2d",
    "warning":       "#f0a500",
}

STYLE_SHEET = f"""
/* ─── Janela Principal ─── */
QMainWindow {{
    background-color: {COLORS['bg_main']};
}}

/* ─── Sidebar ─── */
#sidebar {{
    background-color: {COLORS['bg_sidebar']};
    border-right: 1px solid {COLORS['border']};
}}

#sidebarHeader {{
    background-color: {COLORS['bg_header']};
}}

#logoLabel {{
    color: #ffffff;
    font-size: 32px;
    font-weight: 900;
    letter-spacing: 3px;
    font-family: 'Segoe UI', sans-serif;
}}

#systemLabel {{
    color: rgba(255,255,255,0.6);
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 6px;
    margin-top: 0px;
}}

#subtitleLabel {{
    color: rgba(255,255,255,0.5);
    font-size: 11px;
    margin-top: 8px;
}}

#separator {{
    background-color: {COLORS['border']};
    border: none;
    max-height: 1px;
}}

#catHeader {{
    background-color: transparent;
}}

#sectionTitle {{
    color: {COLORS['text_muted']};
    font-size: 10px;
    font-weight: 700;
    letter-spacing: 3px;
}}

#addCatBtn {{
    background-color: {COLORS['accent_light']};
    color: {COLORS['accent']};
    border: 1px solid {COLORS['accent_light']};
    border-radius: 4px;
    width: 22px;
    height: 22px;
    font-size: 16px;
    font-weight: bold;
    padding: 0;
}}

#addCatBtn:hover {{
    background-color: {COLORS['accent']};
    color: white;
}}

#catList {{
    background-color: transparent;
    border: none;
    outline: none;
    color: {COLORS['text_primary']};
    font-size: 13px;
}}

#catList::item {{
    padding: 10px 16px;
    border-radius: 0;
    border-left: 3px solid transparent;
    color: {COLORS['text_primary']};
}}

#catList::item:hover {{
    background-color: {COLORS['accent_light']};
    color: {COLORS['accent']};
}}

#catList::item:selected {{
    background-color: {COLORS['accent_light']};
    border-left: 3px solid {COLORS['accent']};
    color: {COLORS['accent']};
    font-weight: 600;
}}

#exportWrap {{
    background-color: transparent;
}}

#exportBtn {{
    background-color: {COLORS['accent']};
    color: white;
    border: none;
    border-radius: 6px;
    padding: 10px 16px;
    font-size: 13px;
    font-weight: 600;
}}

#exportBtn:hover {{
    background-color: {COLORS['accent_hover']};
}}

#exportBtn:pressed {{
    background-color: {COLORS['accent_dark']};
}}

/* ─── Área de Conteúdo ─── */
#contentArea {{
    background-color: {COLORS['bg_main']};
}}

#topbar {{
    background-color: {COLORS['bg_topbar']};
    border-bottom: 1px solid {COLORS['border']};
}}

#pageTitle {{
    color: {COLORS['text_primary']};
    font-size: 20px;
    font-weight: 700;
    letter-spacing: 0.5px;
}}

#countLabel {{
    color: {COLORS['text_secondary']};
    font-size: 13px;
    margin-right: 12px;
}}

#addFilBtn {{
    background-color: transparent;
    color: {COLORS['accent']};
    border: 1px solid {COLORS['accent']};
    border-radius: 6px;
    padding: 8px 18px;
    font-size: 13px;
    font-weight: 600;
}}

#addFilBtn:hover {{
    background-color: {COLORS['accent']};
    color: white;
}}

#scrollArea {{
    background-color: {COLORS['bg_main']};
    border: none;
}}

#cardsContainer {{
    background-color: {COLORS['bg_main']};
}}

#placeholder {{
    color: {COLORS['text_muted']};
    font-size: 15px;
    padding: 60px;
}}

/* ─── Cabeçalho da lista ─── */
#listHeader {{
    background-color: {COLORS['bg_topbar']};
    border-bottom: 1px solid {COLORS['border']};
}}

#listHeaderLabel {{
    color: {COLORS['text_muted']};
    font-size: 10px;
    font-weight: 700;
    letter-spacing: 1px;
}}

/* ─── Cards de Filamento ─── */
#filCard {{
    background-color: {COLORS['bg_card']};
    border: 1px solid {COLORS['border']};
    border-radius: 8px;
}}

#filCard:hover {{
    border: 1px solid {COLORS['accent']};
    background-color: #fafbff;
}}

#cardName {{
    color: {COLORS['text_primary']};
    font-size: 13px;
    font-weight: 700;
}}

#cardBrand {{
    color: {COLORS['accent']};
    font-size: 11px;
    font-weight: 500;
}}

#cardMeta {{
    color: {COLORS['text_secondary']};
    font-size: 12px;
}}

#cardTag {{
    background-color: {COLORS['accent_light']};
    color: {COLORS['accent']};
    border-radius: 4px;
    padding: 2px 8px;
    font-size: 11px;
    font-weight: 600;
}}

#cardPreco {{
    color: {COLORS['bg_header']};
    font-size: 13px;
    font-weight: 700;
}}

#cardEditBtn {{
    background-color: #f4f6fb;
    color: {COLORS['text_secondary']};
    border: 1px solid {COLORS['border']};
    font-size: 12px;
    font-weight: 600;
    padding: 4px 12px;
    border-radius: 6px;
}}

#cardEditBtn:hover {{
    background-color: {COLORS['accent_light']};
    color: {COLORS['accent']};
    border: 1px solid {COLORS['accent']};
}}

#cardDeleteBtn {{
    background-color: #f4f6fb;
    color: {COLORS['text_muted']};
    border: 1px solid {COLORS['border']};
    font-size: 14px;
    font-weight: 700;
    padding: 4px 8px;
    border-radius: 6px;
}}

#cardDeleteBtn:hover {{
    background-color: #fdecea;
    color: {COLORS['danger']};
    border: 1px solid #f5b8b8;
}}

#cardImage {{
    border-radius: 6px;
    background-color: {COLORS['bg_main']};
}}

#noImageLabel {{
    color: {COLORS['text_muted']};
    font-size: 24px;
    background-color: {COLORS['bg_main']};
    border-radius: 6px;
}}

/* ─── Diálogos ─── */
QDialog {{
    background-color: {COLORS['bg_card']};
    color: {COLORS['text_primary']};
}}

QLabel {{
    color: {COLORS['text_primary']};
    font-size: 13px;
}}

QLineEdit, QTextEdit, QComboBox {{
    background-color: {COLORS['bg_main']};
    color: {COLORS['text_primary']};
    border: 1px solid {COLORS['border']};
    border-radius: 6px;
    padding: 8px 10px;
    font-size: 13px;
    selection-background-color: {COLORS['accent']};
}}

QLineEdit:focus, QTextEdit:focus, QComboBox:focus {{
    border: 1px solid {COLORS['accent']};
    background-color: #ffffff;
}}

QComboBox::drop-down {{
    border: none;
    padding-right: 8px;
}}

QComboBox QAbstractItemView {{
    background-color: {COLORS['bg_card']};
    color: {COLORS['text_primary']};
    border: 1px solid {COLORS['border']};
    selection-background-color: {COLORS['accent_light']};
    selection-color: {COLORS['accent']};
}}

QPushButton {{
    background-color: {COLORS['accent']};
    color: white;
    border: none;
    border-radius: 6px;
    padding: 9px 20px;
    font-size: 13px;
    font-weight: 600;
}}

QPushButton:hover {{
    background-color: {COLORS['accent_hover']};
}}

QPushButton:pressed {{
    background-color: {COLORS['accent_dark']};
}}

QPushButton[flat=true] {{
    background-color: transparent;
    color: {COLORS['text_secondary']};
    border: 1px solid {COLORS['border']};
}}

QPushButton[flat=true]:hover {{
    background-color: {COLORS['bg_main']};
    color: {COLORS['text_primary']};
}}

QScrollBar:vertical {{
    background: {COLORS['bg_main']};
    width: 8px;
    border-radius: 4px;
}}

QScrollBar::handle:vertical {{
    background: {COLORS['border']};
    border-radius: 4px;
    min-height: 30px;
}}

QScrollBar::handle:vertical:hover {{
    background: {COLORS['accent']};
}}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0;
}}

QStatusBar {{
    background-color: {COLORS['bg_topbar']};
    color: {COLORS['text_muted']};
    font-size: 11px;
    border-top: 1px solid {COLORS['border']};
}}

QMessageBox {{
    background-color: {COLORS['bg_card']};
    color: {COLORS['text_primary']};
}}

QMessageBox QLabel {{
    color: {COLORS['text_primary']};
}}
"""