#!/bin/bash
# awesome-latex-skills test runner
# Usage: ./run_tests.sh [skill_name]

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
FIXTURES="$SCRIPT_DIR/fixtures"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

pass_count=0
fail_count=0

pass() { echo -e "${GREEN}[PASS]${NC} $1"; pass_count=$((pass_count + 1)); }
fail() { echo -e "${RED}[FAIL]${NC} $1"; fail_count=$((fail_count + 1)); }
warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }

check_pdflatex() {
    if command -v pdflatex &>/dev/null; then
        pass "pdflatex found"
        return 0
    else
        warn "pdflatex not found — compile tests will be skipped"
        return 1
    fi
}

test_rescue_compile() {
    echo ""
    echo "=== Testing latex-rescue: Compilation ==="

    local src="$FIXTURES/errors/broken_paper.tex"
    local workdir="$(mktemp -d)"

    cp "$src" "$workdir/broken_paper.tex"
    local orig_dir="$(pwd)"
    cd "$workdir"

    pdflatex -interaction=nonstopmode -file-line-error broken_paper.tex > /dev/null 2>&1 || true

    if [ ! -f broken_paper.log ]; then
        fail "No .log file produced"
        cd "$orig_dir" && rm -rf "$workdir"
        return
    fi
    pass "Compilation produced .log file"

    local total_errors=$(grep -c '^!' broken_paper.log 2>/dev/null || echo "0")
    echo "  Found $total_errors errors in log"

    if [ "$total_errors" -gt 5 ]; then
        pass "Multiple errors detected ($total_errors total)"
    else
        warn "Fewer errors than expected ($total_errors)"
    fi

    cd "$orig_dir" && rm -rf "$workdir"
}

test_rescue_error_catalog_coverage() {
    echo ""
    echo "=== Testing latex-rescue: Error Catalog Coverage ==="

    local catalog="$SCRIPT_DIR/../latex-rescue/references/error-catalog.md"
    local broken="$FIXTURES/errors/broken_paper.tex"

    local typo_count=$(grep -c '|' "$catalog" 2>/dev/null || echo "0")
    if [ "$typo_count" -gt 10 ]; then
        pass "Error catalog has $typo_count table entries"
    else
        fail "Error catalog has only $typo_count table entries"
    fi

    if grep -qi 'Missing \$ inserted\|math.*symbol.*text' "$catalog"; then
        pass "Error catalog covers math mode errors"
    else
        warn "Math mode error coverage could be improved"
    fi

    if grep -qi 'begin.*end.*mismatch\|environment.*mismatch' "$catalog"; then
        pass "Error catalog covers environment mismatches"
    else
        warn "Environment mismatch coverage could be improved"
    fi
}

test_rescue_expected_fix() {
    echo ""
    echo "=== Testing latex-rescue: Expected Fix Consistency ==="

    local broken="$FIXTURES/errors/broken_paper.tex"
    local fixed="$FIXTURES/errors/expected_fixed.tex"

    if [ ! -f "$fixed" ]; then
        fail "expected_fixed.tex not found"
        return
    fi
    pass "expected_fixed.tex exists"

    local fixed_lines=$(wc -l < "$fixed" | tr -d ' ')
    local broken_lines=$(wc -l < "$broken" | tr -d ' ')
    echo "  broken_paper.tex: $broken_lines lines, expected_fixed.tex: $fixed_lines lines"

    if [ "$fixed_lines" -ge "$((broken_lines - 5))" ] && [ "$fixed_lines" -le "$((broken_lines + 5))" ]; then
        pass "Fixed file is similar size to broken file (within 5 lines)"
    else
        warn "Fixed file size differs significantly from broken file"
    fi

    local flagged=$(grep -c 'FLAGGED' "$fixed" 2>/dev/null || echo "0")
    echo "  $flagged items flagged for manual review"
}

test_polish_rules_exist() {
    echo ""
    echo "=== Testing latex-polish: Reference Completeness ==="

    local skill_dir="$SCRIPT_DIR/../latex-polish"

    local refs=(
        "references/academic-phrasebank.md"
        "references/section-anatomy.md"
        "references/style-guardrails.md"
        "references/chinglish-patterns.md"
    )

    for ref in "${refs[@]}"; do
        if [ -f "$skill_dir/$ref" ]; then
            pass "Reference file exists: $ref"
        else
            fail "Missing reference file: $ref"
        fi
    done

    local chinglish="$skill_dir/references/chinglish-patterns.md"
    local line_count=$(wc -l < "$chinglish" | tr -d ' ')
    if [ "$line_count" -gt 100 ]; then
        pass "Chinglish reference has $line_count lines"
    else
        warn "Chinglish reference only has $line_count lines"
    fi
}

test_fmt_templates() {
    echo ""
    echo "=== Testing latex-fmt: Template Coverage ==="

    local guide="$SCRIPT_DIR/../latex-fmt/references/templates/venue-guide.md"

    if [ ! -f "$guide" ]; then
        fail "Venue guide not found"
        return
    fi

    local venues=("NeurIPS" "ICML" "CVPR" "ACL" "IEEE" "Nature" "Science" "AAAI" "ICLR" "ECCV" "TMLR")
    for venue in "${venues[@]}"; do
        if grep -qi "$venue" "$guide"; then
            pass "Venue guide covers: $venue"
        else
            warn "Venue guide may be missing: $venue"
        fi
    done
}

test_paper_read_coverage() {
    echo ""
    echo "=== Testing paper-read: Reference Completeness ==="

    local skill_dir="$SCRIPT_DIR/../paper-read"

    local refs=(
        "references/reading-framework.md"
        "references/critical-appraisal.md"
    )

    for ref in "${refs[@]}"; do
        if [ -f "$skill_dir/$ref" ]; then
            pass "Reference file exists: $ref"
        else
            fail "Missing reference file: $ref"
        fi
    done

    local appraisal="$skill_dir/references/critical-appraisal.md"
    local sections=("Methodology" "Results" "Claims" "Innovation")
    for section in "${sections[@]}"; do
        if grep -qi "$section" "$appraisal"; then
            pass "Critical appraisal covers: $section"
        else
            warn "Critical appraisal may be missing: $section"
        fi
    done
}

test_pdf2tex_coverage() {
    echo ""
    echo "=== Testing pdf2tex: Reference Completeness ==="

    local skill_dir="$SCRIPT_DIR/../pdf2tex"

    local refs=(
        "references/pdf-extraction-guide.md"
        "references/structure-detection.md"
        "references/math-reconstruction.md"
        "references/table-reconstruction.md"
    )

    for ref in "${refs[@]}"; do
        if [ -f "$skill_dir/$ref" ]; then
            pass "Reference file exists: $ref"
        else
            fail "Missing reference file: $ref"
        fi
    done
}

test_agent_configs() {
    echo ""
    echo "=== Testing Agent Configs ==="

    for agent_dir in "$SCRIPT_DIR/../"*/agents; do
        local skill=$(basename "$(dirname "$agent_dir")")
        if [ -f "$agent_dir/config.yaml" ]; then
            pass "$skill has config.yaml"
        else
            fail "$skill missing config.yaml"
        fi

        if grep -q "/$skill" "$agent_dir/config.yaml" 2>/dev/null; then
            pass "$skill config.yaml has slash command trigger"
        else
            fail "$skill config.yaml missing slash command trigger"
        fi
    done
}

test_skill_triggers() {
    echo ""
    echo "=== Testing SKILL.md Trigger Consistency ==="

    for skill_dir in "$SCRIPT_DIR/../"*/; do
        local skill=$(basename "$skill_dir")
        local skill_md="$skill_dir/SKILL.md"
        [ -f "$skill_md" ] || continue

        if grep -q "/$skill" "$skill_md"; then
            pass "$skill SKILL.md has slash command trigger"
        else
            fail "$skill SKILL.md missing slash command trigger"
        fi

        local trigger_count=$(grep -c '^\s*- "' "$skill_md" 2>/dev/null || echo "0")
        if [ "$trigger_count" -ge 5 ]; then
            pass "$skill has $trigger_count triggers"
        else
            warn "$skill has only $trigger_count triggers"
        fi
    done
}

test_chinese_pattern_coverage() {
    echo ""
    echo "=== Testing Chinese Author Pattern Coverage ==="

    local chinglish="$SCRIPT_DIR/../latex-polish/references/chinglish-patterns.md"
    local sample="$FIXTURES/polish/chinglish_sample.tex"

    local categories=(
        "Article Omission"
        "Subject-Verb Agreement"
        "Plural"
        "can"
        "According to"
        "Make.*Let"
        "So.*Conjunction"
        "Wrong Prepositions"
        "Commonly Confused"
        "Redundancy"
    )

    local matched=0
    local total=${#categories[@]}

    for cat in "${categories[@]}"; do
        if grep -qi "$cat" "$chinglish" 2>/dev/null; then
            matched=$((matched + 1))
        fi
    done

    echo "  Reference covers $matched/${total} major pattern categories"
    if [ "$matched" -ge 8 ]; then
        pass "Comprehensive chinglish reference ($matched/10 categories)"
    elif [ "$matched" -ge 5 ]; then
        pass "Adequate chinglish reference ($matched/10 categories)"
    else
        warn "Only $matched/10 categories covered"
    fi
}

# --- Main ---

echo "======================================"
echo " awesome-latex-skills Test Suite"
echo "======================================"
echo ""

HAS_LATEX=false
check_pdflatex && HAS_LATEX=true || true

test_rescue_error_catalog_coverage
test_rescue_expected_fix
test_polish_rules_exist
test_fmt_templates
test_paper_read_coverage
test_pdf2tex_coverage
test_agent_configs
test_skill_triggers
test_chinese_pattern_coverage

if $HAS_LATEX; then
    test_rescue_compile
fi

echo ""
echo "======================================"
printf " Results: \033[0;32m%s passed\033[0m, \033[0;31m%s failed\033[0m\n" "$pass_count" "$fail_count"
echo "======================================"

if [ "$fail_count" -gt 0 ]; then
    exit 1
fi
exit 0
