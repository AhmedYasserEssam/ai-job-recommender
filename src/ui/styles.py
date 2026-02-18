STYLESHEET = """
    QWidget {
        background-color: #0b0e14;
        font-family: 'Segoe UI', 'Roboto', sans-serif;
    }
    QLineEdit {
        background-color: #151923;
        border: 2px solid #2d3436;
        border-radius: 12px;
        color: #00f3ff;
        padding: 15px;
        font-size: 14px;
        selection-background-color: #bc13fe;
    }
    QLineEdit:focus {
        border: 2px solid #00f3ff;
    }
    QScrollBar:vertical {
        border: none;
        background: #0b0e14;
        width: 8px;
        margin: 0px 0px 0px 0px;
    }
    QScrollBar::handle:vertical {
        background: #2d3436;
        min-height: 20px;
        border-radius: 4px;
    }
    QScrollBar::handle:vertical:hover {
        background: #00f3ff;
    }
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
        height: 0px;
    }
"""

COLORS = {
    "cyan": "#00f3ff",
    "purple": "#bc13fe",
    "dark_bg": "#0b0e14",
    "card_bg": "#151923",
    "card_hover": "#1a1e29",
    "border": "#2d3436",
    "muted": "#636e72",
    "text_secondary": "#b2bec3",
    "text": "#ecf0f1",
}
