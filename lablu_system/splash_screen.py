"""
Splash screen do LaBlu System — tema claro, limpo e profissional.
"""

import math
import random
from PyQt6.QtWidgets import QWidget, QApplication
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import (
    QPainter, QColor, QFont, QPen, QLinearGradient,
    QRadialGradient, QBrush, QPainterPath
)

W_SPLASH = 680
H_SPLASH = 390


class SplashScreen(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.SplashScreen
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(W_SPLASH, H_SPLASH)

        screen = QApplication.primaryScreen().geometry()
        self.move(
            (screen.width()  - self.width())  // 2,
            (screen.height() - self.height()) // 2,
        )

        self._fade             = 0.0
        self._progress         = 0.0
        self._shimmer          = 0.0
        self._time             = 0
        self._closing          = False
        self._subtitle_opacity = 0.0

        # Círculos decorativos de fundo (grandes, sutis)
        W, H = W_SPLASH, H_SPLASH
        self._circles = []
        for _ in range(5):
            self._circles.append({
                "x":    random.uniform(W * 0.1, W * 0.9),
                "y":    random.uniform(H * 0.1, H * 0.9),
                "r":    random.uniform(30, 80),
                "phase": random.uniform(0, math.pi * 2),
            })

        # Pré-cria fontes para não recriar a cada frame
        self._font_logo   = QFont("Segoe UI", 68, QFont.Weight.Black)
        self._font_system = QFont("Segoe UI", 10, QFont.Weight.Bold)
        self._font_system.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 10)
        self._font_sub    = QFont("Segoe UI", 12)
        self._font_info   = QFont("Segoe UI", 9)
        self._font_ver    = QFont("Segoe UI", 8)

        self._main_timer = QTimer(self)
        self._main_timer.timeout.connect(self._tick)
        self._main_timer.start(16)

        QTimer.singleShot(5000, self._begin_close)

    def _tick(self):
        self._time += 1

        if not self._closing:
            self._fade = min(1.0, self._fade + 0.04)
            if self._time > 25:
                self._subtitle_opacity = min(1.0, self._subtitle_opacity + 0.03)
        else:
            self._fade = max(0.0, self._fade - 0.055)
            if self._fade <= 0.0:
                self._main_timer.stop()
                self.close()
                return

        if self._time > 18:
            spd = 0.006 if self._progress < 0.83 else 0.003
            self._progress = min(1.0, self._progress + spd)

        self._shimmer = (self._shimmer + 0.018) % 1.0
        self.update()

    def _begin_close(self):
        self._closing = True

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setRenderHint(QPainter.RenderHint.TextAntialiasing)
        p.setOpacity(self._fade)

        W, H = W_SPLASH, H_SPLASH
        corner_r = 18

        # ── Clipping ─────────────────────────────────────────────────
        clip = QPainterPath()
        clip.addRoundedRect(0, 0, W, H, corner_r, corner_r)
        p.setClipPath(clip)

        # ── Fundo branco com gradiente sutil ─────────────────────────
        bg = QLinearGradient(0, 0, 0, H)
        bg.setColorAt(0.0, QColor("#ffffff"))
        bg.setColorAt(1.0, QColor("#f4f8f0"))
        p.fillRect(0, 0, W, H, QBrush(bg))

        # Glow verde bem sutil no centro-topo
        glow = QRadialGradient(W / 2, 0, 320)
        glow.setColorAt(0.0, QColor(79, 153, 0, 28))
        glow.setColorAt(1.0, QColor(0, 0, 0, 0))
        p.fillRect(0, 0, W, H, QBrush(glow))

        # ── Círculos decorativos de fundo ─────────────────────────────
        p.setPen(Qt.PenStyle.NoPen)
        for c in self._circles:
            pulse = (math.sin(self._time * 0.02 + c["phase"]) + 1) / 2
            alpha = int(8 + pulse * 8)
            p.setBrush(QColor(79, 153, 0, alpha))
            p.drawEllipse(
                int(c["x"] - c["r"]), int(c["y"] - c["r"]),
                int(c["r"] * 2), int(c["r"] * 2)
            )

        # ── Faixa verde superior ──────────────────────────────────────
        stripe_g = QLinearGradient(0, 0, W, 0)
        stripe_g.setColorAt(0.0,  QColor(79, 153, 0, 0))
        stripe_g.setColorAt(0.15, QColor(79, 153, 0, 255))
        stripe_g.setColorAt(0.85, QColor(100, 180, 0, 255))
        stripe_g.setColorAt(1.0,  QColor(79, 153, 0, 0))
        p.setBrush(QBrush(stripe_g))
        p.drawRect(0, 0, W, 4)

        # ── Logo "LaBlu" ──────────────────────────────────────────────
        cx = W / 2

        # Sombra do logo
        p.setFont(self._font_logo)
        p.setPen(QColor(0, 0, 0, 12))
        p.drawText(int(cx - 200) + 2, 62 + 3, 400, 110,
                   Qt.AlignmentFlag.AlignCenter, "LaBlu")

        # Logo com gradiente verde
        logo_g = QLinearGradient(cx - 130, 62, cx + 130, 172)
        logo_g.setColorAt(0.0,  QColor("#2d6a00"))
        logo_g.setColorAt(0.45, QColor("#4F9900"))
        logo_g.setColorAt(1.0,  QColor("#3a7800"))
        p.setPen(QPen(QBrush(logo_g), 0))
        p.setFont(self._font_logo)
        p.drawText(int(cx - 200), 62, 400, 110,
                   Qt.AlignmentFlag.AlignCenter, "LaBlu")

        # ── "SYSTEM" ──────────────────────────────────────────────────
        p.setFont(self._font_system)
        p.setPen(QColor(120, 160, 80, 220))
        p.drawText(0, 182, W, 22, Qt.AlignmentFlag.AlignCenter, "S Y S T E M")

        # ── Linha divisória ───────────────────────────────────────────
        div_y = 218
        dg = QLinearGradient(0, div_y, W, div_y)
        dg.setColorAt(0.0,  QColor(79, 153, 0, 0))
        dg.setColorAt(0.2,  QColor(79, 153, 0, 80))
        dg.setColorAt(0.5,  QColor(79, 153, 0, 160))
        dg.setColorAt(0.8,  QColor(79, 153, 0, 80))
        dg.setColorAt(1.0,  QColor(79, 153, 0, 0))
        p.setPen(QPen(QBrush(dg), 1))
        p.drawLine(int(W * 0.18), div_y, int(W * 0.82), div_y)

        # ── Subtítulo ─────────────────────────────────────────────────
        p.setOpacity(self._fade * self._subtitle_opacity)
        p.setFont(self._font_sub)
        p.setPen(QColor(80, 100, 60, 200))
        p.drawText(0, 228, W, 30,
                   Qt.AlignmentFlag.AlignCenter,
                   "Gerenciador de Filamentos & Impressoras 3D")
        p.setOpacity(self._fade)

        # ── Barra de progresso ────────────────────────────────────────
        bar_x = int(W * 0.12)
        bar_y = 310
        bar_w = int(W * 0.76)
        bar_h = 5
        bar_r = 2.5

        # Trilho
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor(0, 0, 0, 14))
        p.drawRoundedRect(bar_x, bar_y, bar_w, bar_h, bar_r, bar_r)

        fill_w = int(bar_w * self._progress)
        if fill_w > 2:
            # Fill
            fg = QLinearGradient(bar_x, 0, bar_x + fill_w, 0)
            fg.setColorAt(0.0, QColor("#2d6a00"))
            fg.setColorAt(0.6, QColor("#4F9900"))
            fg.setColorAt(1.0, QColor("#72c400"))
            p.setBrush(QBrush(fg))
            p.drawRoundedRect(bar_x, bar_y, fill_w, bar_h, bar_r, bar_r)

            # Highlight superior
            hi = QLinearGradient(0, bar_y, 0, bar_y + bar_h)
            hi.setColorAt(0.0, QColor(255, 255, 255, 70))
            hi.setColorAt(1.0, QColor(255, 255, 255, 0))
            p.setBrush(QBrush(hi))
            p.drawRoundedRect(bar_x, bar_y, fill_w, bar_h // 2 + 1, bar_r, bar_r)

            # Shimmer
            if fill_w > 60:
                sh_pos = bar_x + int((fill_w - 60) * (self._shimmer % 1.0))
                sh_g = QLinearGradient(sh_pos, 0, sh_pos + 60, 0)
                sh_g.setColorAt(0.0, QColor(255, 255, 255, 0))
                sh_g.setColorAt(0.5, QColor(255, 255, 255, 100))
                sh_g.setColorAt(1.0, QColor(255, 255, 255, 0))
                p.setBrush(QBrush(sh_g))
                p.drawRoundedRect(sh_pos, bar_y, 60, bar_h, bar_r, bar_r)

        # ── Status + percentual ───────────────────────────────────────
        p.setFont(self._font_info)

        if self._progress < 0.30:
            status = "Inicializando..."
        elif self._progress < 0.60:
            status = "Carregando dados..."
        elif self._progress < 0.88:
            status = "Preparando interface..."
        else:
            status = "Pronto!"

        p.setPen(QColor(100, 140, 60, 180))
        p.drawText(bar_x, bar_y + 11, 180, 18, Qt.AlignmentFlag.AlignLeft, status)

        p.setPen(QColor(60, 110, 20, 200))
        p.drawText(bar_x, bar_y + 11, bar_w, 18, Qt.AlignmentFlag.AlignRight,
                   f"{int(self._progress * 100)}%")

        # ── Versão ────────────────────────────────────────────────────
        p.setFont(self._font_ver)
        p.setPen(QColor(160, 180, 140, 180))
        p.drawText(0, H - 16, W - 18, 14, Qt.AlignmentFlag.AlignRight, "v1.0.0")

        # ── Borda cinza claro ─────────────────────────────────────────
        p.setPen(QPen(QColor(200, 215, 185, 220), 1.0))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawRoundedRect(1, 1, W - 2, H - 2, corner_r, corner_r)

        p.end()

    def mousePressEvent(self, _event):
        self._begin_close()
