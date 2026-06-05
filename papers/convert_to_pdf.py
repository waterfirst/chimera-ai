#!/usr/bin/env python3
"""Convert the final markdown paper to a publication-quality PDF."""

import markdown2
from weasyprint import HTML
import os

PAPER_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_DIR = os.path.dirname(PAPER_DIR)
MD_FILE = os.path.join(PAPER_DIR, "round_number_barrier_final.md")
PDF_FILE = os.path.join(PAPER_DIR, "round_number_barrier_final.pdf")

# Read markdown
with open(MD_FILE, "r", encoding="utf-8") as f:
    md_content = f.read()

# Convert markdown to HTML
html_body = markdown2.markdown(
    md_content,
    extras=["tables", "fenced-code-blocks", "header-ids", "code-friendly"]
)

# Fix image paths to absolute file:// URIs
for img_name in [
    "chart1_indices_round_numbers.png",
    "chart2_rn_distance_volatility.png",
    "chart3_recovery_paths.png",
    "chart4_summary_dashboard.png",
    "kospi_round_number_analysis.png",
    "kospi_correction_pattern.png",
    "kospi_model_dashboard.png",
]:
    abs_path = os.path.join(REPO_DIR, img_name)
    html_body = html_body.replace(f"../{img_name}", f"file://{abs_path}")

# Full HTML with CSS styling
full_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<style>
@page {{
    size: A4;
    margin: 2cm 2cm 2.5cm 2cm;
    @bottom-center {{
        content: counter(page);
        font-size: 9pt;
        color: #555;
    }}
}}
body {{
    font-family: 'DejaVu Serif', 'Noto Serif CJK KR', 'Times New Roman', serif;
    font-size: 10.5pt;
    line-height: 1.55;
    color: #1a1a1a;
    max-width: 100%;
    text-align: justify;
    hyphens: auto;
}}
h1 {{
    font-size: 17pt;
    text-align: center;
    margin-top: 0.5cm;
    margin-bottom: 0.2cm;
    line-height: 1.25;
    color: #111;
}}
h2 {{
    font-size: 13pt;
    border-bottom: 1.5px solid #333;
    padding-bottom: 3pt;
    margin-top: 20pt;
    color: #111;
}}
h3 {{
    font-size: 11.5pt;
    margin-top: 14pt;
    color: #222;
}}
h4 {{
    font-size: 10.5pt;
    margin-top: 10pt;
    color: #333;
}}
p {{
    margin: 6pt 0;
}}
table {{
    border-collapse: collapse;
    width: 100%;
    margin: 10pt 0;
    font-size: 9.5pt;
    page-break-inside: avoid;
}}
th, td {{
    border: 1px solid #999;
    padding: 4pt 6pt;
    text-align: left;
}}
th {{
    background-color: #e8e8e8;
    font-weight: bold;
}}
tr:nth-child(even) {{
    background-color: #f7f7f7;
}}
code {{
    font-family: 'DejaVu Sans Mono', 'Courier New', monospace;
    font-size: 9pt;
    background-color: #f0f0f0;
    padding: 1pt 3pt;
    border-radius: 2pt;
}}
pre {{
    background-color: #f5f5f5;
    border: 1px solid #ddd;
    border-radius: 3pt;
    padding: 8pt;
    font-size: 8.5pt;
    line-height: 1.4;
    overflow-x: auto;
    page-break-inside: avoid;
}}
pre code {{
    background: none;
    padding: 0;
}}
blockquote {{
    border-left: 3pt solid #666;
    margin: 10pt 0;
    padding: 6pt 12pt;
    background-color: #fafafa;
    font-style: italic;
    color: #333;
}}
img {{
    max-width: 100%;
    height: auto;
    display: block;
    margin: 12pt auto;
    border: 1px solid #ddd;
    page-break-inside: avoid;
}}
em {{
    color: #444;
}}
strong {{
    color: #000;
}}
hr {{
    border: none;
    border-top: 1px solid #ccc;
    margin: 16pt 0;
}}
ul, ol {{
    margin: 6pt 0;
    padding-left: 20pt;
}}
li {{
    margin: 3pt 0;
}}
/* Title page styling */
h1 + p {{
    text-align: center;
    font-size: 11pt;
}}
h1 + p + p {{
    text-align: center;
    font-size: 10pt;
    font-style: italic;
}}
</style>
</head>
<body>
{html_body}
</body>
</html>"""

print("Generating PDF...")
HTML(string=full_html, base_url=REPO_DIR).write_pdf(PDF_FILE)
print(f"PDF saved to: {PDF_FILE}")
size_mb = os.path.getsize(PDF_FILE) / (1024 * 1024)
print(f"File size: {size_mb:.1f} MB")
