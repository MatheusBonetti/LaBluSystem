"""
LaBlu System - Gerenciador de Filamentos 3D
Versão 1.0
"""

import sys
import os
import subprocess
import importlib.util
import threading


def _check_and_install_dependencies():
    """Verifica se as dependências estão instaladas; instala as ausentes via pip."""
    requirements_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "requirements.txt")
    if not os.path.exists(requirements_path):
        return

    with open(requirements_path) as f:
        packages = [line.strip() for line in f if line.strip() and not line.startswith("#")]

    # Mapeamento entre nome no pip e nome do módulo para importação
    import_names = {
        "PyQt6": "PyQt6",
        "reportlab": "reportlab",
        "Pillow": "PIL",
    }

    missing = []
    for pkg in packages:
        # Remove versão (ex.: "PyQt6>=6.5.0" → "PyQt6")
        base = pkg.split(">=")[0].split("==")[0].split("<=")[0].strip()
        module = import_names.get(base, base)
        if importlib.util.find_spec(module) is None:
            missing.append(pkg)

    if missing:
        print(f"[LaBlu] Instalando dependências ausentes: {', '.join(missing)}")
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "--quiet"] + missing
        )
        print("[LaBlu] Dependências instaladas com sucesso.")


_check_and_install_dependencies()
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import QTimer
from pathlib import Path
from database import Database
from ui.main_window import MainWindow
from splash_screen import SplashScreen


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("LaBlu System")
    app.setApplicationVersion("1.0")
    app.setStyle("Fusion")

    icon_path = Path(__file__).parent / "BambuLabLogo.ico"
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))

    # ── Evita que o Qt encerre o app quando o splash fechar ──
    app.setQuitOnLastWindowClosed(False)

    # ── Splash screen ──
    splash = SplashScreen()
    splash.show()
    app.processEvents()

    # ── Inicializa DB (rápido — só abre a conexão SQLite) ──
    db = Database()
    db.initialize()

    # ── Comprime imagens em background ──
    threading.Thread(target=db.compress_existing_images, daemon=True).start()

    window_holder = [None]

    def build_window():
        """Cria a janela principal após a splash já estar visível e animando."""
        window_holder[0] = MainWindow(db)

    def show_main():
        if not splash.isVisible() and window_holder[0] is not None:
            window_holder[0].show()
            app.setQuitOnLastWindowClosed(True)
            poll_timer.stop()

    # Dá 1800ms para a splash animar antes de criar a janela pesada
    QTimer.singleShot(1800, build_window)

    poll_timer = QTimer()
    poll_timer.timeout.connect(show_main)
    poll_timer.start(100)

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
