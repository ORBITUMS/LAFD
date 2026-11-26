APP_CSS = """
/* ==================== Базовые переходы ==================== */
.footer, .top-bar, .welcome-container, .glass-dialog {
    transition: background-color 220ms ease, color 220ms ease, border-color 220ms ease;
}

/* ==================== Плавающий стеклянный футер ==================== */
.footer {
    background-color: rgba(24, 24, 28, 0.72);
    border: 1px solid rgba(255, 255, 255, 0.14);
    border-top-color: rgba(255, 255, 255, 0.22);
    border-radius: 20px;
    padding: 5px 6px;
    box-shadow: 0 12px 36px rgba(0, 0, 0, 0.45), inset 0 1px 0 rgba(255, 255, 255, 0.08);
}
.footer.light {
    background-color: rgba(248, 248, 252, 0.78);
    border: 1px solid rgba(0, 0, 0, 0.09);
    border-top-color: rgba(255, 255, 255, 0.95);
    box-shadow: 0 12px 36px rgba(0, 0, 0, 0.14), inset 0 1px 0 rgba(255, 255, 255, 0.9);
}

.h-sessions-scroll {
    background: transparent;
}
.h-sessions-scroll scrollbar {
    opacity: 0;
    min-height: 0;
}

/* Кнопки сессий */
.footer-btn {
    border-radius: 14px;
    padding: 6px 13px;
    min-height: 22px;
    background-color: transparent;
    border: 1px solid transparent;
    color: rgba(255, 255, 255, 0.76);
    font-weight: 500;
    font-size: 13.5px;
    transition: background-color 160ms ease, color 160ms ease, border-color 160ms ease;
}
.footer.light .footer-btn {
    color: rgba(0, 0, 0, 0.72);
}
.footer-btn:hover {
    background-color: rgba(255, 255, 255, 0.09);
    color: #ffffff;
}
.footer.light .footer-btn:hover {
    background-color: rgba(0, 0, 0, 0.06);
    color: #000000;
}
.footer-btn:checked {
    background-color: rgba(255, 255, 255, 0.16);
    border-color: rgba(255, 255, 255, 0.12);
    color: #ffffff;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2), inset 0 1px 0 rgba(255, 255, 255, 0.14);
}
.footer.light .footer-btn:checked {
    background-color: rgba(255, 255, 255, 0.85);
    border-color: rgba(0, 0, 0, 0.06);
    color: #000000;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08), inset 0 1px 0 rgba(255, 255, 255, 0.9);
}

/* Активное перетаскивание вкладки */
.footer-btn.dragging {
    background-color: rgba(10, 132, 255, 0.28);
    border-color: rgba(10, 132, 255, 0.65);
    color: #ffffff;
    box-shadow: 0 6px 18px rgba(10, 132, 255, 0.3);
}
.footer.light .footer-btn.dragging {
    background-color: rgba(0, 122, 255, 0.18);
    border-color: rgba(0, 122, 255, 0.55);
    color: #0051a8;
}

/* Статус-точки активности */
.status-dot {
    min-width: 7px;
    min-height: 7px;
    border-radius: 999px;
    background-color: rgba(160, 160, 168, 0.5);
    transition: background-color 200ms ease, box-shadow 200ms ease;
}
.status-dot.active {
    background-color: #30d158;
    box-shadow: 0 0 8px rgba(48, 209, 88, 0.75);
}
.status-dot.recent {
    background-color: #ffd60a;
    box-shadow: 0 0 7px rgba(255, 214, 10, 0.55);
}
.status-dot.old {
    background-color: rgba(152, 152, 157, 0.55);
}
.status-dot.sleeping {
    background-color: transparent;
    border: 1.5px solid rgba(152, 152, 157, 0.45);
}

.plus-btn, .gear-btn {
    min-width: 34px;
    padding: 6px 8px;
    font-weight: 600;
    font-size: 16px;
    border-radius: 13px;
    background: transparent;
    border: none;
    color: rgba(255, 255, 255, 0.82);
    transition: background-color 140ms ease, color 140ms ease;
}
.footer.light .plus-btn, .footer.light .gear-btn {
    color: rgba(0, 0, 0, 0.78);
}
.plus-btn:hover, .gear-btn:hover {
    background-color: rgba(255, 255, 255, 0.11);
    color: #ffffff;
}
.footer.light .plus-btn:hover, .footer.light .gear-btn:hover {
    background-color: rgba(0, 0, 0, 0.07);
    color: #000000;
}

/* Синий плюсик быстрых ссылок */
.quick-link-btn {
    color: #0a84ff;
    font-weight: 700;
    font-size: 16px;
    min-width: 34px;
    padding: 6px 8px;
    border-radius: 13px;
    background: transparent;
    border: none;
    transition: background-color 140ms ease, box-shadow 160ms ease;
}
.quick-link-btn:hover {
    background-color: rgba(10, 132, 255, 0.16);
    box-shadow: 0 2px 10px rgba(10, 132, 255, 0.22);
}

/* ==================== Верхняя панель ==================== */
.top-bar {
    padding: 4px 10px;
}
.nav-btn {
    border-radius: 10px;
    min-width: 32px;
    min-height: 32px;
    padding: 4px;
    background: transparent;
    border: none;
    transition: background-color 160ms ease;
}
.nav-btn:hover {
    background-color: rgba(255, 255, 255, 0.09);
}
.nav-btn:disabled {
    opacity: 0.28;
}
.top-bar.light .nav-btn:hover {
    background-color: rgba(0, 0, 0, 0.06);
}
.top-bar searchentry {
    border-radius: 11px;
    min-height: 32px;
}

/* Прогресс-бар загрузки */
progressbar.load-progress {
    min-height: 2px;
    margin: 0;
    padding: 0;
}
progressbar.load-progress trough {
    min-height: 2px;
    background: transparent;
    border: none;
}
progressbar.load-progress progress {
    min-height: 2px;
    background-image: linear-gradient(90deg, #0a84ff, #64d2ff);
    border-radius: 0;
}

/* ==================== Премиальные пузыри (Popovers) ==================== */
@keyframes popover-in {
    from {
        opacity: 0;
        transform: translateY(8px) scale(0.96);
    }
    to {
        opacity: 1;
        transform: translateY(0) scale(1);
    }
}

popover.glass-popover > contents {
    background-color: rgba(28, 28, 32, 0.92);
    border-radius: 16px;
    border: 1px solid rgba(255, 255, 255, 0.14);
    border-top-color: rgba(255, 255, 255, 0.2);
    box-shadow: 0 18px 48px rgba(0, 0, 0, 0.58), inset 0 1px 0 rgba(255, 255, 255, 0.08);
    padding: 6px;
    animation: popover-in 180ms cubic-bezier(0.16, 1, 0.3, 1);
}
popover.glass-popover.light > contents {
    background-color: rgba(252, 252, 255, 0.94);
    border: 1px solid rgba(0, 0, 0, 0.09);
    border-top-color: rgba(255, 255, 255, 0.95);
    box-shadow: 0 18px 48px rgba(0, 0, 0, 0.18), inset 0 1px 0 rgba(255, 255, 255, 0.95);
}

/* Поле ввода в пузырях и настройках */
entry.glass-entry {
    background-color: rgba(255, 255, 255, 0.07);
    border: 1px solid rgba(255, 255, 255, 0.12);
    border-radius: 11px;
    padding: 8px 12px;
    color: #ffffff;
    caret-color: #ffffff;
    font-size: 13.5px;
    min-width: 220px;
    transition: border-color 180ms ease, box-shadow 180ms ease, background-color 180ms ease;
}
popover.glass-popover.light entry.glass-entry,
.glass-dialog.light entry.glass-entry {
    background-color: rgba(0, 0, 0, 0.05);
    border-color: rgba(0, 0, 0, 0.14);
    color: #1c1c1e;
    caret-color: #1c1c1e;
}
entry.glass-entry:focus {
    border-color: #0a84ff;
    box-shadow: 0 0 0 3px rgba(10, 132, 255, 0.22);
    outline: none;
}

.popover-header {
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 0.04em;
    color: rgba(255, 255, 255, 0.42);
    padding: 4px 10px 6px;
}
popover.glass-popover.light .popover-header {
    color: rgba(0, 0, 0, 0.42);
}
.popover-sep {
    background-color: rgba(255, 255, 255, 0.09);
    min-height: 1px;
    margin: 4px 6px;
}
popover.glass-popover.light .popover-sep {
    background-color: rgba(0, 0, 0, 0.08);
}

.menu-item-btn {
    border-radius: 10px;
    padding: 7px 12px;
    min-height: 22px;
    background: transparent;
    border: none;
    color: rgba(255, 255, 255, 0.92);
    font-weight: 500;
    font-size: 13.5px;
    transition: background-color 120ms ease, color 120ms ease;
}
popover.glass-popover.light .menu-item-btn {
    color: rgba(0, 0, 0, 0.88);
}
.menu-item-btn:hover {
    background-color: #0a84ff;
    color: #ffffff;
}
.menu-item-btn.destructive {
    color: #ff453a;
}
.menu-item-btn.destructive:hover {
    background-color: #ff453a;
    color: #ffffff;
}

/* ==================== Вертикальный список сессий ==================== */
.v-sessions-list {
    background: transparent;
    padding: 2px;
}
.v-sessions-list row {
    padding: 0;
    margin-bottom: 2px;
    border-radius: 10px;
    background: transparent;
}
.v-sessions-list row:last-child {
    margin-bottom: 0;
}
.v-row-btn {
    padding: 8px 12px;
    min-height: 22px;
    border-radius: 10px;
    background: transparent;
    border: none;
    color: rgba(255, 255, 255, 0.9);
    font-weight: 500;
    font-size: 13.5px;
    transition: background-color 120ms ease, color 120ms ease;
}
popover.glass-popover.light .v-row-btn {
    color: rgba(0, 0, 0, 0.88);
}
.v-row-btn:hover {
    background-color: rgba(255, 255, 255, 0.1);
}
popover.glass-popover.light .v-row-btn:hover {
    background-color: rgba(0, 0, 0, 0.06);
}
.v-row-btn.active-session {
    background-color: rgba(10, 132, 255, 0.16);
    color: #ffffff;
}
popover.glass-popover.light .v-row-btn.active-session {
    background-color: rgba(0, 122, 255, 0.12);
    color: #0051a8;
}

/* ==================== Welcome ==================== */
.welcome-title {
    font-size: 64px;
    font-weight: 800;
    letter-spacing: -0.03em;
    color: rgba(255, 255, 255, 0.95);
}
.welcome-container.light .welcome-title {
    color: rgba(0, 0, 0, 0.9);
}
.welcome-subtitle {
    font-size: 16px;
    color: rgba(255, 255, 255, 0.55);
    margin-top: 6px;
}
.welcome-container.light .welcome-subtitle {
    color: rgba(0, 0, 0, 0.55);
}
.ascii-art {
    font-family: monospace;
    font-size: 11px;
    color: rgba(255, 255, 255, 0.32);
}
.welcome-container.light .ascii-art {
    color: rgba(0, 0, 0, 0.28);
}

/* ==================== Затемнение при первом запуске ==================== */
.onboarding-overlay {
    background-color: rgba(0, 0, 0, 0.82);
}
.onboarding-text {
    font-size: 22px;
    font-weight: 600;
    color: white;
    margin-bottom: 16px;
}

/* ==================== Окно настроек (macOS System Settings) ==================== */
.settings-window {
    background: transparent;
}
.glass-dialog {
    background-color: rgba(26, 26, 30, 0.95);
    border-radius: 22px;
    border: 1px solid rgba(255, 255, 255, 0.14);
    border-top-color: rgba(255, 255, 255, 0.22);
    box-shadow: 0 28px 70px rgba(0, 0, 0, 0.6), inset 0 1px 0 rgba(255, 255, 255, 0.08);
}
.glass-dialog.light {
    background-color: rgba(245, 245, 247, 0.97);
    border-color: rgba(0, 0, 0, 0.09);
    border-top-color: rgba(255, 255, 255, 0.95);
    box-shadow: 0 28px 70px rgba(0, 0, 0, 0.2), inset 0 1px 0 rgba(255, 255, 255, 0.95);
}
.glass-dialog .settings-title {
    font-size: 26px;
    font-weight: 800;
    color: #ffffff;
    letter-spacing: -0.02em;
}
.glass-dialog.light .settings-title {
    color: #1c1c1e;
}
.settings-card {
    background-color: rgba(255, 255, 255, 0.05);
    border: 1px solid rgba(255, 255, 255, 0.07);
    border-radius: 14px;
    padding: 6px 14px;
}
.glass-dialog.light .settings-card {
    background-color: rgba(255, 255, 255, 0.85);
    border-color: rgba(0, 0, 0, 0.06);
}
.glass-dialog .settings-label {
    font-size: 14.5px;
    font-weight: 500;
    color: rgba(255, 255, 255, 0.9);
}
.glass-dialog.light .settings-label {
    color: rgba(0, 0, 0, 0.86);
}
.glass-dialog .settings-sep {
    background-color: rgba(255, 255, 255, 0.07);
    min-height: 1px;
}
.glass-dialog.light .settings-sep {
    background-color: rgba(0, 0, 0, 0.06);
}
.glass-close-btn {
    border-radius: 999px;
    min-width: 32px;
    min-height: 32px;
    padding: 0;
    background-color: rgba(255, 255, 255, 0.08);
    border: none;
    color: rgba(255, 255, 255, 0.72);
    transition: background-color 140ms ease, color 140ms ease;
}
.glass-close-btn image {
    -gtk-icon-size: 16px;
}
.glass-close-btn:hover {
    background-color: rgba(255, 255, 255, 0.16);
    color: #ffffff;
}
.glass-dialog.light .glass-close-btn {
    background-color: rgba(0, 0, 0, 0.06);
    color: rgba(0, 0, 0, 0.6);
}
.glass-dialog.light .glass-close-btn:hover {
    background-color: rgba(0, 0, 0, 0.12);
    color: #000000;
}
.premium-switch {
    min-width: 50px;
    min-height: 28px;
    border-radius: 999px;
    background-color: rgba(255, 255, 255, 0.12);
    border: none;
    transition: background-color 240ms ease;
}
.glass-dialog.light .premium-switch {
    background-color: rgba(0, 0, 0, 0.14);
}
.premium-switch slider {
    min-width: 24px;
    min-height: 24px;
    border-radius: 999px;
    background: #ffffff;
    box-shadow: 0 2px 6px rgba(0, 0, 0, 0.35);
    margin: 2px;
    transition: all 240ms cubic-bezier(0.25, 1, 0.5, 1);
}
.premium-switch:checked,
.glass-dialog.light .premium-switch:checked {
    background-color: #30d158;
}
.premium-btn {
    border-radius: 10px;
    padding: 7px 14px;
    background-color: rgba(10, 132, 255, 0.16);
    border: 1px solid rgba(10, 132, 255, 0.3);
    color: #64b5ff;
    font-weight: 600;
    font-size: 13.5px;
    transition: background-color 140ms ease, box-shadow 140ms ease;
}
.glass-dialog.light .premium-btn {
    background-color: rgba(0, 122, 255, 0.1);
    border-color: rgba(0, 122, 255, 0.28);
    color: #007aff;
}
.premium-btn:hover {
    background-color: rgba(10, 132, 255, 0.26);
    box-shadow: 0 4px 14px rgba(10, 132, 255, 0.25);
}
/* Подпись потребления RAM в вертикальном списке */
.ram-badge {
    font-size: 11px;
    font-weight: 600;
    color: rgba(255, 255, 255, 0.48);
    padding: 1px 6px;
    border-radius: 6px;
    background-color: rgba(255, 255, 255, 0.06);
}
popover.glass-popover.light .ram-badge {
    color: rgba(0, 0, 0, 0.5);
    background-color: rgba(0, 0, 0, 0.05);
}
/* Подсветка окна при перетаскивании файла */
.file-drop-active {
    box-shadow: inset 0 0 0 3px rgba(10, 132, 255, 0.75);
}
"""