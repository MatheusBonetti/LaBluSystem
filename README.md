# LaBlu System

Sistema desktop de gerenciamento de estoque de filamentos 3D e impressoras, desenvolvido para o negócio **BambuLaBlu**.

![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![PyQt6](https://img.shields.io/badge/PyQt6-6.5%2B-green)
![SQLite](https://img.shields.io/badge/SQLite-3-lightgrey)
![License](https://img.shields.io/badge/license-Personal%20Use%20Only-red)

## Funcionalidades

### Filamentos
- Cadastro completo com SKU, código, cor, categoria, preço e quantidade
- Upload de imagem com compressão automática (max 400×400 px)
- Preview de imagem ao passar o mouse sobre o card
- Filtro por categoria na sidebar + busca em tempo real
- Toggle rápido de estoque por checkbox
- Seleção múltipla de cards para ações em lote
- Duplicar filamentos selecionados (com diálogo para ajustar categoria e preço)
- Alterar valores em lote dos selecionados
- Excluir selecionados com confirmação

### Impressoras
- Cadastro e gerenciamento de impressoras por categoria
- Cards com mesmas funcionalidades de seleção e ações em lote

### Exportação PDF
- **Modo Loja** — inclui SKU, código e filamentos esgotados
- **Modo Cliente** — somente filamentos em estoque
- Preview do PDF antes de salvar (abre no visualizador padrão do sistema)
- Exportação de catálogo de impressoras

## Stack

| Tecnologia | Uso |
|---|---|
| Python 3.10+ | Linguagem principal |
| PyQt6 | Interface gráfica |
| SQLite | Banco de dados local |
| ReportLab | Geração de PDFs |
| Pillow | Compressão e manipulação de imagens |

## Instalação

### Pré-requisitos
- Python 3.10 ou superior

### Passos

```bash
# Clone o repositório
git clone https://github.com/seu-usuario/lablu-system.git
cd lablu-system

# Instale as dependências
pip install -r lablu_system/requirements.txt

# Execute o sistema
python lablu_system/main.py
```

## Estrutura do projeto

```
lablu_system/
├── main.py                      # Ponto de entrada, splash screen e inicialização
├── database.py                  # CRUD SQLite (filamentos, impressoras, categorias, imagens)
├── pdf_exporter.py              # Exportação de catálogos PDF de filamentos
├── pdf_exporter_impressoras.py  # Exportação de catálogos PDF de impressoras
├── splash_screen.py             # Splash animado com partículas e barra de progresso
├── requirements.txt             # Dependências Python
├── BambuLabLogo.ico             # Ícone do aplicativo
├── data/
│   └── lablu.db                 # Banco de dados SQLite (gerado automaticamente)
├── images/                      # Imagens dos filamentos (gerado automaticamente)
└── ui/
    ├── main_window.py           # Janela principal (sidebar + lista de cards)
    ├── filamento_card.py        # Card de filamento (hover preview + seleção)
    ├── filamento_dialog.py      # Modal criar/editar filamento
    ├── impressora_card.py       # Card de impressora
    ├── impressora_dialog.py     # Modal criar/editar impressora
    ├── duplicar_dialog.py       # Modal para configurar duplicação
    ├── alterar_valores_dialog.py# Modal para alterar valores em lote
    ├── categoria_dialog.py      # Modal criar/editar categoria
    └── styles.py                # Tema visual centralizado (verde #4F9900)
```

## Banco de dados

O banco SQLite é criado automaticamente em `lablu_system/data/lablu.db` na primeira execução.

- **Soft delete** — registros excluídos são marcados com `ativo = 0`, não removidos fisicamente
- **Imagens** — armazenadas em `lablu_system/images/` como `filamento_{id}.jpg`, comprimidas automaticamente

## Performance

- Cache de `QPixmap` em memória para evitar releitura do disco
- Renderização dos cards em lotes de 30 com `QTimer.singleShot`
- Debounce de 250ms na busca para reduzir consultas
- Compressão de imagens existentes em thread separada na inicialização

## Licença

Uso Pessoal — não é permitido modificar, redistribuir ou usar comercialmente. Veja [LICENSE](LICENSE) para detalhes.
