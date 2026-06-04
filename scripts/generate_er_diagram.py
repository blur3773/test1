from __future__ import annotations

from html import escape
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOCS_DIR = ROOT / "docs"
DOWNLOADS_DIR = Path("/Users/nikitaabalaev/Downloads")


COLORS = {
    "bg": "#f7fbfc",
    "grid": "#e8f1f4",
    "ink": "#1f2937",
    "muted": "#526579",
    "teal": "#008aa3",
    "blue": "#2f78bd",
    "yellow": "#f0c343",
    "red": "#ef6555",
    "green": "#2aa889",
    "purple": "#7367f0",
    "line": "#425466",
    "card": "#ffffff",
    "border": "#c9d8df",
}


ENTITIES = [
    {
        "name": "USERS",
        "title": "users",
        "color": COLORS["teal"],
        "x": 70,
        "y": 120,
        "w": 360,
        "fields": [
            "id INTEGER PK",
            "email VARCHAR(120) UNIQUE",
            "username VARCHAR(80) UNIQUE",
            "password_hash VARCHAR(256)",
            "role ENUM(admin, manager, cashier, client)",
            "is_active BOOLEAN",
            "is_verified BOOLEAN",
            "created_at DATETIME",
            "updated_at DATETIME",
        ],
    },
    {
        "name": "CLIENTS",
        "title": "clients",
        "color": COLORS["green"],
        "x": 70,
        "y": 470,
        "w": 360,
        "fields": [
            "id INTEGER PK",
            "user_id INTEGER FK UNIQUE NULL",
            "first_name VARCHAR(50)",
            "last_name VARCHAR(50)",
            "middle_name VARCHAR(50) NULL",
            "phone VARCHAR(20) NULL",
            "email VARCHAR(120) NULL",
            "created_at DATETIME",
            "updated_at DATETIME",
        ],
    },
    {
        "name": "MANAGER_QUESTIONS",
        "title": "manager_questions",
        "color": COLORS["purple"],
        "x": 70,
        "y": 805,
        "w": 360,
        "fields": [
            "id INTEGER PK",
            "user_id INTEGER FK NULL",
            "manager_id INTEGER FK NULL",
            "name VARCHAR(120)",
            "email VARCHAR(120) NULL",
            "phone VARCHAR(20) NULL",
            "topic VARCHAR(200) NULL",
            "message TEXT",
            "status ENUM(new, resolved)",
            "manager_comment TEXT NULL",
        ],
    },
    {
        "name": "ORDERS",
        "title": "orders",
        "color": COLORS["blue"],
        "x": 625,
        "y": 120,
        "w": 385,
        "fields": [
            "id INTEGER PK",
            "user_id INTEGER FK",
            "client_id INTEGER FK NULL",
            "manager_id INTEGER FK NULL",
            "sale_id INTEGER FK UNIQUE NULL",
            "total_amount NUMERIC(10,2)",
            "status ENUM(pending, completed, rejected, cancelled)",
            "customer_comment TEXT NULL",
            "manager_comment TEXT NULL",
            "created_at / updated_at DATETIME",
        ],
    },
    {
        "name": "ORDER_ITEMS",
        "title": "order_items",
        "color": COLORS["blue"],
        "x": 625,
        "y": 520,
        "w": 385,
        "fields": [
            "id INTEGER PK",
            "order_id INTEGER FK",
            "book_id INTEGER FK",
            "quantity INTEGER",
            "price NUMERIC(10,2)",
            "subtotal NUMERIC(10,2)",
        ],
    },
    {
        "name": "SALES",
        "title": "sales",
        "color": COLORS["red"],
        "x": 625,
        "y": 815,
        "w": 385,
        "fields": [
            "id INTEGER PK",
            "cashier_id INTEGER FK",
            "client_id INTEGER FK NULL",
            "total_amount NUMERIC(10,2)",
            "status ENUM(completed, returned, cancelled)",
            "created_at DATETIME",
            "updated_at DATETIME",
        ],
    },
    {
        "name": "BOOKS",
        "title": "books",
        "color": COLORS["yellow"],
        "x": 1230,
        "y": 120,
        "w": 410,
        "fields": [
            "id INTEGER PK",
            "title VARCHAR(200)",
            "title_ru VARCHAR(200) NULL",
            "author VARCHAR(100)",
            "isbn VARCHAR(20) UNIQUE",
            "publisher VARCHAR(100) NULL",
            "year INTEGER NULL",
            "genre VARCHAR(255) NULL",
            "price NUMERIC(10,2)",
            "status ENUM(active, archived)",
            "cover_url / source_url VARCHAR NULL",
            "created_at / updated_at DATETIME",
        ],
    },
    {
        "name": "BOOK_STOCKS",
        "title": "book_stocks",
        "color": COLORS["yellow"],
        "x": 1230,
        "y": 565,
        "w": 410,
        "fields": [
            "id INTEGER PK",
            "book_id INTEGER FK UNIQUE",
            "quantity INTEGER",
            "reserved INTEGER",
            "available = quantity - reserved",
            "updated_at DATETIME",
        ],
    },
    {
        "name": "SALE_ITEMS",
        "title": "sale_items",
        "color": COLORS["red"],
        "x": 1230,
        "y": 815,
        "w": 410,
        "fields": [
            "id INTEGER PK",
            "sale_id INTEGER FK",
            "book_id INTEGER FK",
            "quantity INTEGER",
            "price NUMERIC(10,2)",
            "subtotal NUMERIC(10,2)",
        ],
    },
]


ENTITY_BY_NAME = {entity["name"]: entity for entity in ENTITIES}


RELATIONSHIPS = [
    ("USERS", "CLIENTS", "1", "0..1", "profile: clients.user_id", [(250, 370), (250, 470)]),
    ("USERS", "ORDERS", "1", "0..*", "buyer: orders.user_id", [(430, 215), (545, 215), (545, 210), (625, 210)]),
    ("USERS", "ORDERS", "1", "0..*", "manager: orders.manager_id", [(430, 305), (560, 305), (560, 315), (625, 315)]),
    ("CLIENTS", "ORDERS", "1", "0..*", "orders.client_id", [(430, 560), (520, 560), (520, 360), (625, 360)]),
    ("ORDERS", "ORDER_ITEMS", "1", "1..*", "order rows", [(817, 400), (817, 520)]),
    ("BOOKS", "ORDER_ITEMS", "1", "0..*", "order_items.book_id", [(1230, 320), (1100, 320), (1100, 620), (1010, 620)]),
    ("BOOKS", "BOOK_STOCKS", "1", "1", "stock record", [(1435, 480), (1435, 565)]),
    ("ORDERS", "SALES", "0..1", "0..1", "orders.sale_id", [(930, 400), (930, 455), (1035, 455), (1035, 910), (1010, 910)]),
    ("USERS", "SALES", "1", "0..*", "cashier: sales.cashier_id", [(430, 335), (500, 335), (500, 850), (625, 850)]),
    ("CLIENTS", "SALES", "1", "0..*", "sales.client_id", [(430, 640), (540, 640), (540, 935), (625, 935)]),
    ("SALES", "SALE_ITEMS", "1", "1..*", "sale rows", [(1010, 910), (1230, 910)]),
    ("BOOKS", "SALE_ITEMS", "1", "0..*", "sale_items.book_id", [(1640, 355), (1695, 355), (1695, 930), (1640, 930)]),
    ("USERS", "MANAGER_QUESTIONS", "1", "0..*", "question author", [(135, 370), (135, 805)]),
    ("USERS", "MANAGER_QUESTIONS", "1", "0..*", "assigned manager", [(360, 370), (360, 805)]),
]


def entity_height(entity: dict) -> int:
    return 62 + len(entity["fields"]) * 27 + 18


def svg_text(x: int, y: int, text: str, size: int = 16, weight: int = 400, fill: str | None = None) -> str:
    return (
        f'<text x="{x}" y="{y}" font-family="Arial, Helvetica, sans-serif" '
        f'font-size="{size}" font-weight="{weight}" fill="{fill or COLORS["ink"]}">'
        f"{escape(text)}</text>"
    )


def box(entity: dict) -> str:
    x, y, w = entity["x"], entity["y"], entity["w"]
    h = entity_height(entity)
    color = entity["color"]
    parts = [
        f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="10" fill="{COLORS["card"]}" stroke="{COLORS["border"]}" stroke-width="2"/>',
        f'<rect x="{x}" y="{y}" width="{w}" height="48" rx="10" fill="{color}"/>',
        f'<rect x="{x}" y="{y + 34}" width="{w}" height="14" fill="{color}"/>',
        svg_text(x + 18, y + 31, entity["title"], 22, 700, "#ffffff"),
    ]
    row_y = y + 75
    for field in entity["fields"]:
        if " PK" in field:
            fill = COLORS["ink"]
            weight = 700
        elif " FK" in field:
            fill = COLORS["blue"]
            weight = 600
        else:
            fill = COLORS["muted"]
            weight = 400
        parts.append(svg_text(x + 20, row_y, field, 15, weight, fill))
        row_y += 27
    return "\n".join(parts)


def label(x: float, y: float, text: str) -> str:
    width = max(120, len(text) * 7 + 24)
    return "\n".join(
        [
            f'<rect x="{x - width / 2:.1f}" y="{y - 17:.1f}" width="{width}" height="28" rx="6" fill="#ffffff" stroke="#d7e3e8" stroke-width="1"/>',
            f'<text x="{x:.1f}" y="{y + 2:.1f}" text-anchor="middle" font-family="Arial, Helvetica, sans-serif" font-size="13" font-weight="600" fill="{COLORS["line"]}">{escape(text)}</text>',
        ]
    )


def relation(points: list[tuple[int, int]], left_card: str, right_card: str, title: str) -> str:
    path = " ".join(("M" if i == 0 else "L") + f" {x} {y}" for i, (x, y) in enumerate(points))
    mid = points[len(points) // 2]
    start = points[0]
    end = points[-1]
    return "\n".join(
        [
            f'<path d="{path}" fill="none" stroke="{COLORS["line"]}" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"/>',
            f'<circle cx="{start[0]}" cy="{start[1]}" r="4" fill="{COLORS["line"]}"/>',
            f'<circle cx="{end[0]}" cy="{end[1]}" r="4" fill="{COLORS["line"]}"/>',
            svg_text(start[0] + 8, start[1] - 8, left_card, 13, 700, COLORS["line"]),
            svg_text(end[0] + 8, end[1] - 8, right_card, 13, 700, COLORS["line"]),
            label(mid[0], mid[1] - 18, title),
        ]
    )


def build_svg() -> str:
    width, height = 1810, 1180
    grid = []
    for x in range(40, width, 40):
        grid.append(f'<line x1="{x}" y1="0" x2="{x}" y2="{height}" stroke="{COLORS["grid"]}" stroke-width="1"/>')
    for y in range(40, height, 40):
        grid.append(f'<line x1="0" y1="{y}" x2="{width}" y2="{y}" stroke="{COLORS["grid"]}" stroke-width="1"/>')

    rels = [relation(points, left_card, right_card, title) for _, _, left_card, right_card, title, points in RELATIONSHIPS]
    boxes = [box(entity) for entity in ENTITIES]
    legend = "\n".join(
        [
            '<rect x="70" y="38" width="580" height="52" rx="8" fill="#ffffff" stroke="#d7e3e8" stroke-width="1"/>',
            svg_text(92, 70, "PK — первичный ключ, FK — внешний ключ, 1 / 0..1 / 0..* — кратность связи", 18, 600, COLORS["ink"]),
        ]
    )
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
  <rect width="100%" height="100%" fill="{COLORS["bg"]}"/>
  <g opacity="0.65">
    {' '.join(grid)}
  </g>
  {svg_text(70, 28, "ER-диаграмма базы данных BookStore", 26, 800, COLORS["ink"])}
  {legend}
  <g id="relationships">
    {' '.join(rels)}
  </g>
  <g id="entities">
    {' '.join(boxes)}
  </g>
</svg>
"""


def build_mermaid() -> str:
    return """erDiagram
    USERS ||--o| CLIENTS : "profile"
    USERS ||--o{ ORDERS : "buyer"
    USERS ||--o{ ORDERS : "manager"
    CLIENTS ||--o{ ORDERS : "places"
    ORDERS ||--|{ ORDER_ITEMS : "contains"
    BOOKS ||--o{ ORDER_ITEMS : "ordered"
    BOOKS ||--|| BOOK_STOCKS : "has stock"
    ORDERS o|--o| SALES : "creates sale"
    USERS ||--o{ SALES : "cashier"
    CLIENTS ||--o{ SALES : "buyer"
    SALES ||--|{ SALE_ITEMS : "contains"
    BOOKS ||--o{ SALE_ITEMS : "sold"
    USERS ||--o{ MANAGER_QUESTIONS : "asks"
    USERS ||--o{ MANAGER_QUESTIONS : "answers"

    USERS {
        int id PK
        string email UK
        string username UK
        string password_hash
        enum role
        bool is_active
        bool is_verified
        datetime created_at
        datetime updated_at
    }

    CLIENTS {
        int id PK
        int user_id FK_UK
        string first_name
        string last_name
        string phone
        string email
        datetime created_at
        datetime updated_at
    }

    BOOKS {
        int id PK
        string title
        string title_ru
        string author
        string isbn UK
        string publisher
        int year
        string genre
        decimal price
        enum status
        string cover_url
        string source_url
    }

    BOOK_STOCKS {
        int id PK
        int book_id FK_UK
        int quantity
        int reserved
        int available
        datetime updated_at
    }

    ORDERS {
        int id PK
        int user_id FK
        int client_id FK
        int manager_id FK
        int sale_id FK_UK
        decimal total_amount
        enum status
        text customer_comment
        text manager_comment
    }

    ORDER_ITEMS {
        int id PK
        int order_id FK
        int book_id FK
        int quantity
        decimal price
        decimal subtotal
    }

    SALES {
        int id PK
        int cashier_id FK
        int client_id FK
        decimal total_amount
        enum status
        datetime created_at
        datetime updated_at
    }

    SALE_ITEMS {
        int id PK
        int sale_id FK
        int book_id FK
        int quantity
        decimal price
        decimal subtotal
    }

    MANAGER_QUESTIONS {
        int id PK
        int user_id FK
        int manager_id FK
        string name
        string email
        string phone
        string topic
        text message
        enum status
        text manager_comment
    }
"""


def main() -> None:
    DOCS_DIR.mkdir(exist_ok=True)
    DOWNLOADS_DIR.mkdir(exist_ok=True)

    svg = build_svg()
    mermaid = build_mermaid()

    outputs = [
        DOCS_DIR / "bookstore_er_diagram.svg",
        DOWNLOADS_DIR / "bookstore_er_diagram.svg",
    ]
    for output in outputs:
        output.write_text(svg, encoding="utf-8")

    mermaid_outputs = [
        DOCS_DIR / "bookstore_er_diagram.mmd",
        DOWNLOADS_DIR / "bookstore_er_diagram.mmd",
    ]
    for output in mermaid_outputs:
        output.write_text(mermaid, encoding="utf-8")

    print("created:")
    for output in [*outputs, *mermaid_outputs]:
        print(output)


if __name__ == "__main__":
    main()
