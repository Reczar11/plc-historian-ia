"""Global theme loader.

QSS has no variables, so the .qss files use @tokens that are replaced
with the values below before the stylesheet is applied. To add a light
theme later: create aveva_light.qss and a second palette in THEMES.
"""
from pathlib import Path

THEME_DIR = Path(__file__).parent

THEMES = {
    'aveva_dark': {
        'bg': '#1e1e1e',          # window / canvas
        'panel': '#252526',       # trees, tables, inputs
        'panel_alt': '#2d2d30',   # headers, toolbars, buttons
        'border': '#3c3c3c',
        'text': '#e0e0e0',
        'text_dim': '#9a9a9a',
        'accent': '#4ec9b0',
        'select': '#094771',
        'hover': '#3c3c3c',
        'danger': '#f48771',
    },
}

DEFAULT_THEME = 'aveva_dark'


def build_stylesheet(name=DEFAULT_THEME):
    qss = (THEME_DIR / f'{name}.qss').read_text(encoding='utf-8')
    # Longest tokens first so @text_dim is not clobbered by @text
    for key in sorted(THEMES[name], key=len, reverse=True):
        qss = qss.replace('@' + key, THEMES[name][key])
    return qss


def apply_theme(app, name=DEFAULT_THEME):
    app.setStyle('Fusion')  # same base look on Mac/Windows/Linux
    app.setStyleSheet(build_stylesheet(name))


def color(token, name=DEFAULT_THEME):
    return THEMES[name][token]
