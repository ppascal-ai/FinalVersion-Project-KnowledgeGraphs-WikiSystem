#!/usr/bin/env python3
"""Generate PNG diagrams for docs/diagrams from the validated schema/architecture.

This simple script uses Pillow to draw diagrams that match the draw.io layouts
so the repo contains PNG exports that are readable and stylistically consistent.
"""
from PIL import Image, ImageDraw, ImageFont
import os


def ensure_dir(path):
    d = os.path.dirname(path)
    if d and not os.path.exists(d):
        os.makedirs(d)


def draw_neo4j_schema(path):
    w, h = 1400, 800
    bg = (43, 43, 43)
    img = Image.new("RGB", (w, h), bg)
    draw = ImageDraw.Draw(img)

    # Fonts (fallback)
    try:
        font_b = ImageFont.truetype("DejaVuSans-Bold.ttf", 16)
        font = ImageFont.truetype("DejaVuSans.ttf", 14)
    except Exception:
        font_b = ImageFont.load_default()
        font = ImageFont.load_default()

    # Node rectangles
    def rounded_rect(x, y, wbox, hbox, radius, fill, outline):
        draw.rounded_rectangle([x, y, x + wbox, y + hbox], radius=radius, fill=fill, outline=outline, width=2)

    # Author
    rounded_rect(100, 260, 260, 120, 12, fill=(46, 123, 180), outline=(31, 90, 134))
    draw.multiline_text((120, 280), "Author\nwikidata_id (UNIQUE)\nname", font=font, fill=(255, 255, 255))

    # Article
    rounded_rect(480, 230, 360, 140, 12, fill=(88, 166, 58), outline=(62, 126, 42))
    draw.multiline_text((500, 250), "Article (Film)\nwikidata_id (UNIQUE)\ntitle\nyear (optional)", font=font, fill=(255, 255, 255))

    # Topic
    rounded_rect(980, 260, 240, 120, 12, fill=(229, 138, 29), outline=(184, 106, 18))
    draw.multiline_text((1000, 280), "Topic (Genre)\nname (UNIQUE)", font=font, fill=(255, 255, 255))

    # Arrows
    draw.line((360, 320, 480, 320), fill=(255, 255, 255), width=3)
    draw.polygon([(480, 320), (470, 315), (470, 325)], fill=(255, 255, 255))
    draw.text((380, 300), "DIRECTED", font=font_b, fill=(255, 255, 255))

    draw.line((840, 300, 980, 300), fill=(255, 255, 255), width=3)
    draw.polygon([(980, 300), (970, 295), (970, 305)], fill=(255, 255, 255))
    draw.text((880, 280), "HAS_TOPIC", font=font_b, fill=(255, 255, 255))

    # Legend box
    rounded_rect(1160, 40, 220, 200, 8, fill=(58, 58, 58), outline=(85, 85, 85))
    legend = (
        "Constraints & Indexes\n\n"
        "Unique constraints:\n"
        "• Article.wikidata_id\n"
        "• Author.wikidata_id\n"
        "• Topic.name\n\n"
        "Indexes (non-unique):\n"
        "• Article.title\n"
        "• Article.year\n"
        "• Author.name"
    )
    draw.multiline_text((1180, 60), legend, font=font, fill=(255, 255, 255))

    ensure_dir(path)
    img.save(path, format="PNG")


def draw_architecture(path):
    w, h = 1400, 900
    bg = (245, 245, 245)
    img = Image.new("RGB", (w, h), bg)
    draw = ImageDraw.Draw(img)

    try:
        font_b = ImageFont.truetype("DejaVuSans-Bold.ttf", 14)
        font = ImageFont.truetype("DejaVuSans.ttf", 12)
    except Exception:
        font_b = ImageFont.load_default()
        font = ImageFont.load_default()

    # User actor
    draw.ellipse((40, 120, 120, 200), fill=(245, 245, 245), outline=(102, 102, 102), width=2)
    draw.text((40, 205), "User / Client", font=font, fill=(0, 0, 0))

    # API
    draw.rounded_rectangle((200, 140, 520, 360), radius=8, fill=(213, 232, 212), outline=(130, 179, 102), width=2)
    api_text = (
        "FastAPI Service (api)\n\nPort: 8000\n\nEndpoints:\n"
        "• /health\n"
        "• /api/search\n"
        "• /api/articles/{film_id}/related\n"
        "• /api/topics/{topic}/graph\n"
        "• /api/authors/{director_id}/contributions\n"
        "• /docs"
    )
    draw.multiline_text((220, 160), api_text, font=font, fill=(0, 0, 0))

    # Neo4j
    draw.rounded_rectangle((720, 140, 1040, 360), radius=8, fill=(255, 242, 204), outline=(214, 182, 86), width=2)
    neo_text = "Neo4j Database (neo4j)\n\nPorts:\n• 7687 (Bolt)\n• 7474 (Browser)"
    draw.multiline_text((740, 160), neo_text, font=font_b, fill=(0, 0, 0))

    # Seed & Import scripts
    draw.rounded_rectangle((180, 420, 420, 580), radius=8, fill=(225, 213, 231), outline=(150, 115, 166), width=2)
    draw.multiline_text((200, 440), "Seed Script\n(scripts/seed_data.py)\n\nCreates schema / constraints / indexes\n(no wipe by default)", font=font, fill=(0, 0, 0))

    draw.rounded_rectangle((460, 420, 700, 580), radius=8, fill=(219, 234, 247), outline=(108, 147, 191), width=2)
    draw.multiline_text((480, 440), "Import Wikidata\n(scripts/import_wikidata.py)\n\nSPARQL -> Neo4j", font=font, fill=(0, 0, 0))

    # Arrows
    draw.line((120, 160, 200, 220), fill=(130, 179, 102), width=3)
    draw.polygon([(200, 220), (190, 215), (190, 225)], fill=(130, 179, 102))

    draw.line((520, 250, 720, 250), fill=(214, 182, 86), width=3)
    draw.polygon([(720, 250), (710, 245), (710, 255)], fill=(214, 182, 86))

    draw.line((300, 560, 720, 260), fill=(150, 115, 166), width=3)
    draw.polygon([(720, 260), (712, 252), (712, 268)], fill=(150, 115, 166))

    draw.line((580, 560, 720, 300), fill=(108, 147, 191), width=3)
    draw.polygon([(720, 300), (712, 292), (712, 308)], fill=(108, 147, 191))

    ensure_dir(path)
    img.save(path, format="PNG")


if __name__ == "__main__":
    # generate images in docs/diagrams
    draw_neo4j_schema("docs/diagrams/neo4j_schema.png")
    draw_architecture("docs/diagrams/architecture.png")
    print("Generated: docs/diagrams/neo4j_schema.png and docs/diagrams/architecture.png")
