#!/bin/bash

# LWE Expanded Features GUI - Test Runner Script
# This script provides convenient commands for running different test suites

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$SCRIPT_DIR"
TESTS_DIR="$PROJECT_ROOT/tests"
SOURCE_DIR="$PROJECT_ROOT/source"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Print colored output
print_header() {
    echo -e "${BLUE}=== $1 ===${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_info() {
    echo -e "${YELLOW}ℹ $1${NC}"
}

# Check dependencies
check_dependencies() {
    local missing=0
    
    print_header "Checking Dependencies"
    
    # Check Python
    if ! command -v python3 &> /dev/null; then
        print_error "Python3 not found"
        missing=1
    else
        print_success "Python3 found"
    fi
    
    # Check pytest
    if ! python3 -m pytest --version &> /dev/null; then
        print_error "pytest not installed"
        missing=1
    else
        print_success "pytest found: $(python3 -m pytest --version)"
    fi
    
    # Check BATS
    if ! command -v bats &> /dev/null; then
        print_info "BATS not found (optional, for bash tests only)"
    else
        print_success "BATS found"
    fi
    
    if [ $missing -eq 1 ]; then
        echo
        print_error "Missing dependencies. Run: pip install -r requirements-test.txt"
        return 1
    fi
    
    return 0
}

# Run all tests
run_all_tests() {
    print_header "Running All Tests"
    export PYTHONPATH="$SOURCE_DIR:$PYTHONPATH"
    
    python3 -m pytest "$TESTS_DIR" -v --tb=short
    
    if command -v bats &> /dev/null; then
        print_header "Running Bash Tests (BATS)"
        bats "$TESTS_DIR/test_main.sh" -v
    fi
}

# Run Python tests only
run_python_tests() {
    print_header "Running Python Tests"
    export PYTHONPATH="$SOURCE_DIR:$PYTHONPATH"
    
    python3 -m pytest "$TESTS_DIR" -v --tb=short -m "not backend" "$@"
}

# Run backend (bash) tests only
run_backend_tests() {
    print_header "Running Backend (Bash) Tests"
    
    if ! command -v bats &> /dev/null; then
        print_error "BATS not installed. Run: sudo apt-get install bats"
        return 1
    fi
    
    bats "$TESTS_DIR/test_main.sh" -v "$@"
}

# Run config tests only
run_config_tests() {
    print_header "Running Configuration Tests"
    export PYTHONPATH="$SOURCE_DIR:$PYTHONPATH"
    
    python3 -m pytest "$TESTS_DIR/test_config.py" -v --tb=short "$@"
}

# Run engine controller tests only
run_engine_tests() {
    print_header "Running Engine Controller Tests"
    export PYTHONPATH="$SOURCE_DIR:$PYTHONPATH"
    
    python3 -m pytest "$TESTS_DIR/test_engine_controller.py" -v --tb=short "$@"
}

# Run UI component tests only
run_ui_tests() {
    print_header "Running UI Component Tests"
    export PYTHONPATH="$SOURCE_DIR:$PYTHONPATH"
    
    python3 -m pytest "$TESTS_DIR/test_ui_components.py" -v --tb=short "$@"
}

# Run unit tests only
run_unit_tests() {
    print_header "Running Unit Tests"
    export PYTHONPATH="$SOURCE_DIR:$PYTHONPATH"
    
    python3 -m pytest "$TESTS_DIR" -v --tb=short -m "unit" "$@"
}

# Run integration tests only
run_integration_tests() {
    print_header "Running Integration Tests"
    export PYTHONPATH="$SOURCE_DIR:$PYTHONPATH"
    
    python3 -m pytest "$TESTS_DIR" -v --tb=short -m "integration" "$@"
}

# Run with coverage report
run_with_coverage() {
    print_header "Running Tests with Coverage"
    export PYTHONPATH="$SOURCE_DIR:$PYTHONPATH"
    
    python3 -m pytest "$TESTS_DIR" \
        --cov="$SOURCE_DIR" \
        --cov-report=html \
        --cov-report=term-missing \
        -v --tb=short "$@"
    
    print_success "Coverage report generated in htmlcov/index.html"
}

# Run tests in parallel
run_parallel_tests() {
    print_header "Running Tests in Parallel"
    export PYTHONPATH="$SOURCE_DIR:$PYTHONPATH"
    
    if ! python3 -m pytest --version | grep -q xdist; then
        print_error "pytest-xdist not installed. Run: pip install pytest-xdist"
        return 1
    fi
    
    python3 -m pytest "$TESTS_DIR" -n auto -v --tb=short "$@"
}

# Generate HTML report
generate_html_report() {
    print_header "Generating HTML Test Report"
    export PYTHONPATH="$SOURCE_DIR:$PYTHONPATH"
    
    python3 -m pytest "$TESTS_DIR" \
        --html=test-report.html \
        --self-contained-html \
        -v --tb=short "$@"
    
    print_success "Test report generated: test-report.html"
}

# Show test statistics
show_test_stats() {
    print_header "Test Statistics"
    export PYTHONPATH="$SOURCE_DIR:$PYTHONPATH"
    
    echo "Python test files:"
    find "$TESTS_DIR" -name "test_*.py" -type f | while read -r file; do
        count=$(grep -c "def test_\|@pytest\|def.*test" "$file" || echo "0")
        basename=$(basename "$file")
        printf "  %-30s %3d tests\n" "$basename" "$count"
    done
    
    if [ -f "$TESTS_DIR/test_main.sh" ]; then
        count=$(grep -c "^@test" "$TESTS_DIR/test_main.sh" || echo "0")
        printf "  %-30s %3d tests\n" "test_main.sh" "$count"
    fi
    
    total=$(find "$TESTS_DIR" -name "test_*.py" -type f -exec grep -c "def test_\|@pytest" {} + | awk '{sum+=$1} END {print sum}')
    if [ -f "$TESTS_DIR/test_main.sh" ]; then
        bash_tests=$(grep -c "^@test" "$TESTS_DIR/test_main.sh" || echo "0")
        total=$((total + bash_tests))
    fi
    
    echo
    echo -e "${BLUE}Total tests: ${GREEN}$total${NC}"
}

# Run specific test
run_specific_test() {
    local test_name="$1"
    
    if [ -z "$test_name" ]; then
        print_error "Please provide test name"
        return 1
    fi
    
    print_header "Running Specific Test: $test_name"
    export PYTHONPATH="$SOURCE_DIR:$PYTHONPATH"
    
    python3 -m pytest "$TESTS_DIR" -k "$test_name" -v --tb=short
}

# Install dependencies
install_dependencies() {
    print_header "Installing Test Dependencies"
    
    if [ -f "$PROJECT_ROOT/requirements-test.txt" ]; then
        pip install -r "$PROJECT_ROOT/requirements-test.txt"
        print_success "Dependencies installed"
    else
        print_error "requirements-test.txt not found"
        return 1
    fi
    
    # Try to install BATS
    if ! command -v bats &> /dev/null; then
        print_info "Installing BATS..."
        if command -v apt-get &> /dev/null; then
            sudo apt-get update
            sudo apt-get install -y bats
        elif command -v brew &> /dev/null; then
            brew install bats-core
        fi
    fi
}

# Show help
show_help() {
    cat << EOF
${BLUE}LWE Expanded Features GUI - Test Runner${NC}

${GREEN}Usage:${NC}
  ./run_tests.sh [command] [options]

${GREEN}Commands:${NC}
  all              Run all tests (Python + Bash)
  python           Run Python tests only
  backend          Run backend (Bash) tests only
  config           Run configuration tests only
  engine           Run engine controller tests only
  ui               Run UI component tests only
  unit             Run unit tests only
  integration      Run integration tests only
  coverage         Run tests with coverage report
  parallel         Run tests in parallel (faster)
  html             Generate HTML test report
  stats            Show test statistics
  test [name]      Run specific test by name/pattern
  install          Install test dependencies
  check            Check test dependencies
  help             Show this help message

${GREEN}Examples:${NC}
  # Run all tests
  ./run_tests.sh all

  # Run with coverage
  ./run_tests.sh coverage

  # Run specific test
  ./run_tests.sh test test_load_config

  # Run only unit tests
  ./run_tests.sh unit

  # Run config and engine tests
  ./run_tests.sh config engine

  # Run all tests with verbose output
  ./run_tests.sh python -vv

${GREEN}Options:${NC}
  -v, -vv         Verbose output (more -v = more verbose)
  -x               Stop on first failure
  --tb=short       Short traceback format
  --pdb            Drop into debugger on failure
  -s               Show print statements

${GREEN}Environment:${NC}
  PYTHONPATH       Set automatically to include source directory
  PYTHONDONTWRITEBYTECODE  Disable .pyc file generation

EOF
}

# Main script logic
main() {
    # Check if no arguments provided
    if [ $# -eq 0 ]; then
        show_help
        exit 0
    fi
    
    # Parse commands
    while [ $# -gt 0 ]; do
        case "$1" in
            all)
                check_dependencies || exit 1
                run_all_tests
                shift
                ;;
            python)
                check_dependencies || exit 1
                shift
                run_python_tests "$@"
                break
                ;;
            backend)
                check_dependencies || exit 1
                shift
                run_backend_tests "$@"
                break
                ;;
            config)
                check_dependencies || exit 1
                shift
                run_config_tests "$@"
                break
                ;;
            engine)
                check_dependencies || exit 1
                shift
                run_engine_tests "$@"
                break
                ;;
            ui)
                check_dependencies || exit 1
                shift
                run_ui_tests "$@"
                break
                ;;
            unit)
                check_dependencies || exit 1
                shift
                run_unit_tests "$@"
                break
                ;;
            integration)
                check_dependencies || exit 1
                shift
                run_integration_tests "$@"
                break
                ;;
            coverage)
                check_dependencies || exit 1
                shift
                run_with_coverage "$@"
                break
                ;;
            parallel)
                check_dependencies || exit 1
                shift
                run_parallel_tests "$@"
                break
                ;;
            html)
                check_dependencies || exit 1
                shift
                generate_html_report "$@"
                break
                ;;
            stats)
                show_test_stats
                shift
                ;;
            test)
                check_dependencies || exit 1
                shift
                run_specific_test "$@"
                break
                ;;
            install)
                install_dependencies
                shift
                ;;
            check)
                check_dependencies
                shift
                ;;
            help|-h|--help)
                show_help
                shift
                ;;
            *)
                print_error "Unknown command: $1"
                show_help
                exit 1
                ;;
        esac
    done
}

# Run main function
main "$@"
