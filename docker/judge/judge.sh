#!/bin/bash
# EduAgent Online Judge Sandbox Runner
# Usage: judge.sh <lang> <code_file> <test_dir> <time_limit_sec> <memory_limit_kb>
# Returns JSON result to stdout

LANG="$1"
CODE_FILE="$2"
TEST_DIR="$3"
TIME_LIMIT="${4:-2}"
MEM_LIMIT="${5:-262144}"

# ── Helper: output JSON and exit ──
output_json() {
  echo "$1"
  exit 0
}

# ── Helper: normalize output (trim trailing whitespace, normalize newlines) ──
normalize() {
  sed 's/[[:space:]]*$//' | sed 's/\r$//'
}

# ── Compile ──
compile() {
  case "$LANG" in
    c)
      gcc -Wall -O2 -o /tmp/prog "$CODE_FILE" 2>/tmp/compile_err.txt
      return $?
      ;;
    cpp)
      g++ -Wall -O2 -std=c++17 -o /tmp/prog "$CODE_FILE" 2>/tmp/compile_err.txt
      return $?
      ;;
    java)
      javac -d /tmp "$CODE_FILE" 2>/tmp/compile_err.txt
      return $?
      ;;
    python)
      python3 -c "import py_compile; py_compile.compile('$CODE_FILE', doraise=True)" 2>/tmp/compile_err.txt
      return $?
      ;;
    *)
      echo '{"status":"CE","compile_error":"Unsupported language: '"$LANG"'","results":[],"passed":0,"total":0}'
      exit 0
      ;;
  esac
}

# ── Run single test case ──
run_test() {
  local input_file="$1"
  local test_index="$2"
  local start_time end_time elapsed

  start_time=$(date +%s%N)

  # Run the program with timeout
  if [ "$LANG" = "python" ]; then
    timeout "$TIME_LIMIT" python3 "$CODE_FILE" < "$input_file" > /tmp/actual_out.txt 2>/tmp/run_err.txt
  elif [ "$LANG" = "java" ]; then
    timeout "$TIME_LIMIT" java -cp /tmp Main < "$input_file" > /tmp/actual_out.txt 2>/tmp/run_err.txt
  else
    timeout "$TIME_LIMIT" /tmp/prog < "$input_file" > /tmp/actual_out.txt 2>/tmp/run_err.txt
  fi

  local exit_code=$?
  end_time=$(date +%s%N)
  elapsed=$(( (end_time - start_time) / 1000000 ))  # ms

  # Check for timeout (timeout returns 124)
  if [ $exit_code -eq 124 ]; then
    echo "TLE|${elapsed}|0"
    return
  fi

  # Check for runtime error (non-zero exit)
  if [ $exit_code -ne 0 ]; then
    echo "RE|${elapsed}|0"
    return
  fi

  echo "OK|${elapsed}|0"
}

# ── Generate final JSON ──
generate_json() {
  local status="$1"
  local passed="$2"
  local total="$3"
  shift 3
  local results_json="$*"

  echo "{"
  echo "  \"status\": \"$status\","
  echo "  \"passed\": $passed,"
  echo "  \"total\": $total,"
  echo "  \"results\": ["

  local first=true
  for result in $results_json; do
    local case_status=$(echo "$result" | cut -d'|' -f1)
    local case_time=$(echo "$result" | cut -d'|' -f2)
    local case_mem=$(echo "$result" | cut -d'|' -f3)

    [ "$first" = true ] || echo ","
    first=false

    local case_status_label
    case "$case_status" in
      OK)  case_status_label="Accepted" ;;
      WA)  case_status_label="WrongAnswer" ;;
      TLE) case_status_label="TimeLimitExceeded" ;;
      RE)  case_status_label="RuntimeError" ;;
      *)   case_status_label="$case_status" ;;
    esac

    echo -n "    {\"case_id\": $(( ${#results_json[@]} )), \"status\": \"$case_status_label\", \"time_ms\": $case_time, \"memory_kb\": $case_mem}"
  done

  echo ""
  echo "  ],"
  echo "  \"compile_error\": null"
  echo "}"
}

# ═══════════════════════════════════════════════════
# Main
# ═══════════════════════════════════════════════════

# Compile first
if ! compile; then
  compile_err=$(cat /tmp/compile_err.txt 2>/dev/null | head -20)
  # Escape for JSON
  compile_err_json=$(echo "$compile_err" | python3 -c "import sys,json; print(json.dumps(sys.stdin.read()))" 2>/dev/null || echo "\"Compilation failed\"")
  echo "{\"status\":\"CompileError\",\"passed\":0,\"total\":0,\"results\":[],\"compile_error\":$compile_err_json}"
  exit 0
fi

# Run each test case
TOTAL=0
PASSED=0
RESULTS=()

for input_file in "$TEST_DIR"/input_*.txt; do
  [ -f "$input_file" ] || continue
  TOTAL=$((TOTAL + 1))

  test_index="${input_file##*/input_}"
  test_index="${test_index%.txt}"
  expected_file="$TEST_DIR/expected_${test_index}.txt"

  result_line=$(run_test "$input_file" "$test_index")
  case_status=$(echo "$result_line" | cut -d'|' -f1)

  if [ "$case_status" = "OK" ]; then
    # Compare output
    if [ -f "$expected_file" ]; then
      actual_norm=$(cat /tmp/actual_out.txt | normalize)
      expected_norm=$(cat "$expected_file" | normalize)

      if [ "$actual_norm" = "$expected_norm" ]; then
        PASSED=$((PASSED + 1))
        RESULTS+=("OK|$(echo "$result_line" | cut -d'|' -f2)|0")
      else
        RESULTS+=("WA|$(echo "$result_line" | cut -d'|' -f2)|0")
      fi
    else
      # No expected file, count as passed if no error
      PASSED=$((PASSED + 1))
      RESULTS+=("OK|$(echo "$result_line" | cut -d'|' -f2)|0")
    fi
  else
    RESULTS+=("$result_line")
  fi
done

# Determine overall status
if [ $TOTAL -eq 0 ]; then
  STATUS="Accepted"
elif [ $PASSED -eq $TOTAL ]; then
  STATUS="Accepted"
else
  # Check if any are TLE or RE
  HAS_TLE=false
  HAS_RE=false
  for r in "${RESULTS[@]}"; do
    case $(echo "$r" | cut -d'|' -f1) in
      TLE) HAS_TLE=true ;;
      RE) HAS_RE=true ;;
    esac
  done

  if $HAS_RE; then
    STATUS="RuntimeError"
  elif $HAS_TLE; then
    STATUS="TimeLimitExceeded"
  else
    STATUS="WrongAnswer"
  fi
fi

generate_json "$STATUS" "$PASSED" "$TOTAL" "${RESULTS[@]}"
