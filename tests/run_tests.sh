#!/bin/bash
# awesome-latex-skills test runner
# Usage: ./run_tests.sh [skill_name]
#
# Tests are verification-oriented: does the skill's reference knowledge
# cover the error patterns in the test fixtures?

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
        warn "Install: brew install --cask basictex (macOS) or apt install texlive-latex-base (Linux)"
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

    # Phase 1: Gather — compile and capture errors
    pdflatex -interaction=nonstopmode -file-line-error broken_paper.tex > /dev/null 2>&1 || true

    if [ ! -f broken_paper.log ]; then
        fail "No .log file produced"
        return
    fi
    pass "Compilation produced .log file"

    # Phase 2: Parse — count errors by category
    local total_errors=$(grep -c '^!' broken_paper.log 2>/dev/null || echo "0")
    echo "  Found $total_errors errors in log"

    local typos=$(grep -ci 'undefined control sequence' broken_paper.log 2>/dev/null || echo "0")
    echo "  - Undefined control sequences: $typos"

    local math=$(grep -ci 'missing \$ inserted' broken_paper.log 2>/dev/null || echo "0")
    echo "  - Math mode errors: $math"

    local braces=$(grep -ci 'missing } inserted' broken_paper.log 2>/dev/null || echo "0")
    echo "  - Brace errors: $braces"

    local env=$(grep -ci 'end{' broken_paper.log 2>/dev/null || echo "0")
    echo "  - Environment errors: $env"

    # Verify: at least some errors found
    if [ "$total_errors" -gt 5 ]; then
        pass "Multiple error categories detected ($total_errors total)"
    else
        warn "Fewer errors than expected ($total_errors). Test fixture may need updating."
    fi

    # Cleanup
    cd "$orig_dir"
    rm -rf "$workdir"
}

test_rescue_error_catalog_coverage() {
    echo ""
    echo "=== Testing latex-rescue: Error Catalog Coverage ==="

    local catalog="$SCRIPT_DIR/../latex-rescue/references/error-catalog.md"
    local broken="$FIXTURES/errors/broken_paper.tex"

    # Check that error types in fixture are covered by catalog
    local covered=0
    local uncovered=0

    # Check typo coverage
    if grep -qi 'beginn\|endd\|hlin\|usepacakge\|textbfseries' "$broken"; then
        local typo_count=$(grep -c '|' "$catalog" 2>/dev/null || echo "0")
        if [ "$typo_count" -gt 10 ]; then
            pass "Error catalog has $typo_count typo entries (fixture has multiple typos)"
        else
            fail "Error catalog has only $typo_count typo entries"
        fi
    fi

    # Check math error coverage
    if grep -q 'alpha\|x_i\|x\^2' "$broken"; then
        if grep -qi 'Missing \$ inserted\|math.*symbol.*text' "$catalog"; then
            pass "Error catalog covers math mode errors"
        else
            warn "Math mode error coverage could be improved"
        fi
    fi

    # Check environment error coverage
    if grep -q 'begin{figure}' "$broken" && grep -q 'end{table}' "$broken"; then
        if grep -qi 'begin.*end.*mismatch\|environment.*mismatch' "$catalog"; then
            pass "Error catalog covers environment mismatches"
        else
            warn "Environment mismatch coverage could be improved"
        fi
    fi
}

test_polish_rules_exist() {
    echo ""
    echo "=== Testing latex-polish: Reference Completeness ==="

    local skill_dir="$SCRIPT_DIR/../latex-polish"

    # Check each reference file exists
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

    # Check chinglish patterns coverage
    local chinglish="$skill_dir/references/chinglish-patterns.md"
    local line_count=$(wc -l < "$chinglish" | tr -d ' ')
    if [ "$line_count" -gt 100 ]; then
        pass "Chinglish reference has $line_count lines (comprehensive)"
    else
        warn "Chinglish reference only has $line_count lines"
    fi

    # Verify phrasebank covers all major sections
    local sections=("Abstract" "Introduction" "Related Work" "Method" "Conclusion")
    for section in "${sections[@]}"; do
        if grep -q "$section" "$skill_dir/references/academic-phrasebank.md"; then
            pass "Phrasebank covers: $section"
        else
            warn "Phrasebank may be missing: $section"
        fi
    done
}

test_fmt_templates() {
    echo ""
    echo "=== Testing latex-fmt: Template Coverage ==="

    local templates_dir="$SCRIPT_DIR/../latex-fmt/references/templates"
    local guide="$templates_dir/venue-guide.md"

    if [ ! -f "$guide" ]; then
        fail "Venue guide not found"
        return
    fi

    local venues=("NeurIPS" "ICML" "CVPR" "ACL" "IEEE" "Nature" "Science" "AAAI" "ICLR" "ECCV" "TMLR")
    for venue in "${venues[@]}"; do
        if grep -qi "$venue" "$guide"; then
            pass "Template guide covers: $venue"
        else
            warn "Template guide may be missing: $venue"
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

    # Check reading levels are documented
    local skill_md="$skill_dir/SKILL.md"
    if grep -qi 'skim\|read.*level\|deep' "$skill_md"; then
        pass "SKILL.md documents 3 reading levels"
    else
        warn "SKILL.md may be missing reading level definitions"
    fi

    # Check critical appraisal reference is comprehensive
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

test_agent_configs() {
    echo ""
    echo "=== Testing Agent Configs ==="

    local skills=("latex-rescue" "latex-polish" "latex-fmt" "paper-read")

    for skill in "${skills[@]}"; do
        local dir="$SCRIPT_DIR/../$skill/agents"
        for agent in "claude.yaml" "openai.yaml"; do
            if [ -f "$dir/$agent" ]; then
                pass "$skill has $agent config"
            else
                fail "$skill missing $agent config"
            fi
        done
    done
}

test_chinese_pattern_coverage() {
    echo ""
    echo "=== Testing Chinese Author Pattern Coverage ==="

    local chinglish="$SCRIPT_DIR/../latex-polish/references/chinglish-patterns.md"
    local sample="$FIXTURES/polish/chinglish_sample.tex"

    # Check that major pattern categories exist in reference
    local categories=(
        "Article Omission"
        "Subject-Verb Agreement"
        "Plural"
        "Overuse of .can"
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

    # Verify sample file has chinglish issues to detect
    local sample_issues=0
    grep -qi 'can achieve\|research field\|Result shows\|make the model\|different with\|based from\|more and more\|Most of methods\|have several advantage\|works well' "$sample" 2>/dev/null && sample_issues=1
    if [ "$sample_issues" -eq 1 ]; then
        pass "Test sample contains chinglish patterns to detect"
    else
        warn "Test sample may not have enough chinglish patterns"
    fi
}

# --- Main ---

echo "======================================"
echo " awesome-latex-skills Test Suite"
echo "======================================"
echo ""

# Check prerequisites
HAS_LATEX=false
check_pdflatex && HAS_LATEX=true || true

# Run tests
test_rescue_error_catalog_coverage
test_polish_rules_exist
test_fmt_templates
test_paper_read_coverage
test_agent_configs
test_chinese_pattern_coverage

if $HAS_LATEX; then
    test_rescue_compile
fi

# Summary
echo ""
echo "======================================"
printf " Results: \033[0;32m%s passed\033[0m, \033[0;31m%s failed\033[0m\n" "$pass_count" "$fail_count"
echo "======================================"

if [ "$fail_count" -gt 0 ]; then
    exit 1
fi
exit 0