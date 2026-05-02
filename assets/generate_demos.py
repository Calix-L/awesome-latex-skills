"""
Generate terminal-style demo images for awesome-latex-skills.
Creates before/after PNGs showing skills in action.
"""
import os
from PIL import Image, ImageDraw, ImageFont

ASSETS = os.path.dirname(os.path.abspath(__file__))
W, H = 720, 420
BG = "#1a1b26"
FG = "#a9b1d6"
GREEN = "#9ece6a"
RED = "#f7768e"
CYAN = "#7dcfff"
YELLOW = "#e0af68"
MAGENTA = "#bb9af7"
GRAY = "#565f89"
WHITE = "#c0caf5"
ORANGE = "#ff9e64"

PROMPT = f"{GREEN}❯{WHITE}"

FONT_PATH = "/System/Library/Fonts/Menlo.ttc"
try:
    FONT = ImageFont.truetype(FONT_PATH, 13)
    FONT_SM = ImageFont.truetype(FONT_PATH, 11)
    FONT_BOLD = ImageFont.truetype(FONT_PATH, 14)
except Exception:
    FONT = ImageFont.load_default()
    FONT_SM = FONT
    FONT_BOLD = FONT


def make_terminal(title, lines, outpath):
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)

    # Title bar
    d.rectangle([(0, 0), (W, 28)], fill="#3b4261")
    dots = [(10, 14), (28, 14), (46, 14)]
    for dot in dots:
        d.ellipse([(dot[0]-6, dot[1]-6), (dot[0]+6, dot[1]+6)], fill=GRAY)
    d.text((W//2 - len(title)//2 * 7, 6), title, fill=WHITE, font=FONT_SM)

    # Content
    y = 38
    for line in lines:
        if not line:
            y += 6
            continue
        # Handle color tokens
        if isinstance(line, tuple):
            color, text = line
            d.text((14, y), text, fill=color, font=FONT)
        else:
            d.text((14, y), line, fill=FG, font=FONT)
        y += 20
        if y > H - 20:
            break

    os.makedirs(os.path.dirname(outpath), exist_ok=True)
    img.save(outpath, "PNG")
    print(f"  -> {outpath}")


# ── latex-rescue ──────────────────────────────────────────────

# Before: showing compilation errors
make_terminal("Terminal — latex-rescue (before)", [
    (GRAY, "$ pdflatex -interaction=nonstopmode paper.tex"),
    "",
    (RED, "! Undefined control sequence."),
    (FG,  "l.42  This is a \\textbff{bold} statement."),
    (CYAN, "? "),
    "",
    (RED, "! Missing $ inserted."),
    (FG,  "l.58  The variable x_i is important."),
    (CYAN, "? "),
    "",
    (RED, "! LaTeX Error: \\begin{figure} on line 23 ended by \\end{table}."),
    (FG,  "l.67  \\end{table}"),
    "",
    (GRAY, "...47 errors total. Compilation failed."),
], os.path.join(ASSETS, "rescue-before.png"))


# After: showing successful fix + recompile
make_terminal("Terminal — latex-rescue (after)", [
    (GREEN, "Agent: Running /latex-rescue..."),
    "",
    (GRAY, "Phase 1: Compiling with pdflatex..."),
    (GRAY, "Phase 2: Parsed 47 errors -> 3 categories"),
    "",
    (CYAN, "[Auto-fix] l.42: \\textbff -> \\textbf"),
    (CYAN, "[Auto-fix] l.58: x_i -> $x_i$"),
    (CYAN, "[Auto-fix] l.67: \\end{table} -> \\end{figure}"),
    "",
    (GRAY, "Phase 4: Recompiling..."),
    "",
    (GREEN, "Output written on paper.pdf (3 pages, 0 errors) ✓"),
    (WHITE, "Summary: 3 typos fixed. Paper compiles successfully."),
], os.path.join(ASSETS, "rescue-after.png"))


# ── latex-polish ──────────────────────────────────────────────

make_terminal("Terminal — latex-polish (before)", [
    (GRAY, "$ cat method.tex | head -10"),
    "",
    (FG, "The model can achieves good performance on"),
    (FG, "the dataset. According to the experiment,"),
    (YELLOW, "          ^^            ^^^^^^^^^^^^^^"),
    (FG, "it makes the accuracy improved by 3.2%."),
    (FG, "Most of methods in this research field"),
    (YELLOW, "       ^^           ^^^^^^^^^^^^^^^"),
    (FG, "can not achieve the same result."),
    (YELLOW, "^^^^^^^^^^^^^"),
    "",
    (GRAY, "6 Chinglish patterns detected"),
], os.path.join(ASSETS, "polish-before.png"))


make_terminal("Terminal — latex-polish (after)", [
    (GREEN, "Agent: Running /latex-polish --level moderate..."),
    "",
    (CYAN, "[Line 1] 'can achieves' -> 'achieves'"),
    (CYAN, "         (remove modal + verb agreement)"),
    (CYAN, "[Line 1] 'According to the experiment,'"),
    (CYAN, "         -> 'Experiments show that'"),
    (CYAN, "[Line 2] 'makes the accuracy improved'"),
    (CYAN, "         -> 'improves accuracy'"),
    (CYAN, "[Line 3] 'Most of methods' -> 'Most methods'"),
    (CYAN, "[Line 3] 'research field' -> 'field'"),
    (CYAN, "[Line 4] 'can not achieve' -> 'fail to achieve'"),
    "",
    (GREEN, "6/6 issues resolved. Readability: moderate ✓"),
], os.path.join(ASSETS, "polish-after.png"))


# ── latex-fmt ─────────────────────────────────────────────────

make_terminal("Terminal — latex-fmt", [
    (GREEN, "Agent: Running /latex-fmt --venue NeurIPS..."),
    "",
    (GRAY, "Phase 1: Detecting current format... CVPR"),
    (GRAY, "Phase 2: Applying NeurIPS 2025 template..."),
    "",
    (CYAN, "\\documentclass{article} -> \\documentclass{neurips_2025}"),
    (CYAN, "[PACKAGES] Removed: fixmath, cite"),
    (CYAN, "[PACKAGES] Added:   times, cleveref"),
    (CYAN, "[SECTIONS] Removed: Acknowledgements"),
    (CYAN, "[ANONYM] Strip author block, add \\usepackag{neurips_anonymous}"),
    "",
    (GRAY, "Phase 5: 9-page paper -> fits NeurIPS 9-page limit ✓"),
    (GREEN, "NeurIPS compliance checklist: 12/12 ✓"),
], os.path.join(ASSETS, "fmt-demo.png"))


# ── paper-read ────────────────────────────────────────────────

make_terminal("Terminal — /paper-read arxiv.org/abs/2307.xxxxx", [
    (GREEN, "Agent: Running /paper-read --level read..."),
    "",
    (CYAN, "=== Paper Analysis: Training Compute-Optimal LLMs ==="),
    (WHITE, "Authors: Hoffmann et al., DeepMind | NeurIPS 2022"),
    "",
    (WHITE, "TL;DR:"),
    (FG,  "Current LLMs are undertrained. For compute-optimal training,"),
    (FG,  "model size and token count should scale equally. Chinchilla"),
    (FG,  "beats Gopher (4x larger) by training on 4x more data."),
    "",
    (YELLOW, "Key Result: +7% over Gopher with 1/4 the params"),
    (GREEN,  "Strength: Rigorous across 400+ training runs"),
    (RED,    "Weakness: Only tested on English; unknown for MoE"),
    (MAGENTA, "Takeaway: Train on more tokens before making bigger models"),
], os.path.join(ASSETS, "paper-read-demo.png"))


print(f"\nGenerated {4} demo images -> assets/")


# ── pdf2tex ──────────────────────────────────────────────────

make_terminal("Terminal — /pdf2tex paper.pdf", [
    (GREEN, "Agent: Running /pdf2tex paper.pdf..."),
    "",
    (GRAY, "Phase 1: Extracting content with pymupdf..."),
    (GRAY, "  Engine detected: pdflatex (pdfTeX-1.40.25)"),
    (GRAY, "  Fonts: CMR10, CMBX12, CMMI10, CMSY10"),
    "",
    (GRAY, "Phase 2: Analyzing structure..."),
    (CYAN, "  Document class: article (10pt, single-column)"),
    (CYAN, "  5 sections, 3 subsections detected"),
    (CYAN, "  12 equations, 4 tables, 6 figures"),
    "",
    (GRAY, "Phase 3: Reconstructing LaTeX..."),
    (CYAN, "  Preamble generated (amsmath, booktabs, graphicx)"),
    (CYAN, "  4 images extracted -> figures/"),
    (CYAN, "  28 citations mapped -> \\cite{ref1}..\\cite{ref28}"),
    "",
    (GRAY, "Phase 5: Compilation check..."),
    (GREEN, "Output written on paper_reconstructed.pdf (8 pages)"),
    (YELLOW, "2 items flagged for manual review (see .tex comments)"),
], os.path.join(ASSETS, "pdf2tex-demo.png"))

print(f"\nGenerated {5} demo images -> assets/")