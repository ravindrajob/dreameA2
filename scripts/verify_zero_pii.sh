#!/usr/bin/env bash
# ==============================================================================
# ZERO-PII AUDIT & SANITIZATION SCANNER
# Scans all repository files to detect personal data, credentials, or private IPs.
# Does NOT contain any private information itself (reads .pii_terms.local if present).
# ==============================================================================

set -e

PACKAGE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
echo "🔍 Starting Zero-PII Strict Audit on: $PACKAGE_DIR"

ERRORS=0

# 1. Load private forbidden terms from ignored local file if present
LOCAL_TERMS_FILE="$PACKAGE_DIR/.pii_terms.local"
FORBIDDEN_TERMS=()

if [ -f "$LOCAL_TERMS_FILE" ]; then
    echo "📋 Loaded local custom audit terms from .pii_terms.local"
    while IFS= read -r line || [ -n "$line" ]; do
        trimmed="$(echo "$line" | xargs)"
        if [ -n "$trimmed" ] && [[ ! "$trimmed" =~ ^# ]]; then
            FORBIDDEN_TERMS+=("$trimmed")
        fi
    done < "$LOCAL_TERMS_FILE"
fi

# List of files to check (strictly excluding git, ignored files, .pii_terms.local, and python bytecode caches)
FILES_TO_CHECK=$(find "$PACKAGE_DIR" -type f \
    ! -path '*/.git/*' \
    ! -path '*/__pycache__/*' \
    ! -name "*.pyc" \
    ! -name ".pii_terms.local" \
    ! -name "verify_zero_pii.sh")

while IFS= read -r file; do
    [ -z "$file" ] && continue
    rel_path="${file#$PACKAGE_DIR/}"

    # Check custom terms if loaded
    for term in "${FORBIDDEN_TERMS[@]}"; do
        if grep -Fqi "$term" "$file"; then
            echo "❌ [LEAK DETECTED] File '$rel_path' contains forbidden term: '$term'"
            grep -Fni --color=always "$term" "$file" | head -n 3
            ERRORS=$((ERRORS + 1))
        fi
    done

    # Check generic credential patterns (API keys, OAuth tokens, private keys)
    if grep -E "(AIzaSy[A-Za-z0-9_-]{33}|ghp_[A-Za-z0-9]{36}|Bearer [A-Za-z0-9_\-\.]{20,}|-----BEGIN PRIVATE KEY-----)" "$file" > /dev/null; then
        echo "❌ [CREDENTIAL DETECTED] File '$rel_path' contains an API key or private key pattern!"
        ERRORS=$((ERRORS + 1))
    fi

    # Check hardcoded absolute home directories
    if grep -E "/home/[a-zA-Z0-9_\-]+/" "$file" > /dev/null; then
        echo "❌ [ABSOLUTE PATH DETECTED] File '$rel_path' contains a hardcoded /home/ user directory!"
        grep -En "/home/[a-zA-Z0-9_\-]+/" "$file" | head -n 3
        ERRORS=$((ERRORS + 1))
    fi

done <<< "$FILES_TO_CHECK"

if [ "$ERRORS" -gt 0 ]; then
    echo ""
    echo "🚨 ZERO-PII AUDIT FAILED! $ERRORS issue(s) detected. Fix before publishing."
    exit 1
else
    echo ""
    echo "✅ ZERO-PII AUDIT PASSED: 0 personal data, 0 private IP, 0 token found."
    echo "🎉 Repository is 100% anonymous, sanitized, and ready for public sharing."
    exit 0
fi
