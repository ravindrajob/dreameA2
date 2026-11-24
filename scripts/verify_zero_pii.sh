#!/usr/bin/env bash
# ==============================================================================
# ZERO-PII AUDIT & SANITIZATION SCANNER
# Scans repository files to detect personal data, credentials, private RFC 1918
# IPv4 addresses, or hardcoded user home paths before sharing custom builds.
# Reads optional gitignored .pii_terms.local for custom personal keywords.
# ==============================================================================

set -euo pipefail

PACKAGE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
echo "Starting Zero-PII Strict Audit on: $PACKAGE_DIR"

ERRORS=0

# 1. Load optional private forbidden terms from gitignored local file
LOCAL_TERMS_FILE="$PACKAGE_DIR/.pii_terms.local"
FORBIDDEN_TERMS=()

if [ -f "$LOCAL_TERMS_FILE" ]; then
    echo "Loaded local custom audit terms from .pii_terms.local"
    while IFS= read -r line || [ -n "$line" ]; do
        trimmed="$(echo "$line" | xargs)"
        if [ -n "$trimmed" ] && [[ ! "$trimmed" =~ ^# ]]; then
            FORBIDDEN_TERMS+=("$trimmed")
        fi
    done < "$LOCAL_TERMS_FILE"
fi

# List files to check (excluding git, bytecode, vendorized libs, images, self)
FILES_TO_CHECK=$(find "$PACKAGE_DIR" -type f \
    ! -path '*/.git/*' \
    ! -path '*/__pycache__/*' \
    ! -path '*/.pytest_cache/*' \
    ! -path '*/web/vendor/*' \
    ! -path '*/tests/*' \
    ! -name "*.pyc" \
    ! -name "*.webp" \
    ! -name "*.png" \
    ! -name "*.jpg" \
    ! -name ".pii_terms.local" \
    ! -name "verify_zero_pii.sh")

while IFS= read -r file; do
    [ -z "$file" ] && continue
    rel_path="${file#$PACKAGE_DIR/}"

    for term in "${FORBIDDEN_TERMS[@]}"; do
        if grep -Fqi "$term" "$file"; then
            echo "[FAIL][LEAK] '$rel_path' contains forbidden term: '$term'"
            ERRORS=$((ERRORS + 1))
        fi
    done

    # Check RFC 1918 private IPv4 ranges (10.0.0.0/8, 172.16.0.0/12, 192.168.0.0/16)
    # RFC 5737 documentation range (192.0.2.x) and loopback (127.0.0.1) remain permitted.
    if grep -En '\b(10\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}|192\.168\.[0-9]{1,3}\.[0-9]{1,3}|172\.(1[6-9]|2[0-9]|3[01])\.[0-9]{1,3}\.[0-9]{1,3})\b' "$file" > /dev/null; then
        echo "[FAIL][PRIVATE-IP] '$rel_path' contains an RFC 1918 private IPv4 address!"
        grep -En '\b(10\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}|192\.168\.[0-9]{1,3}\.[0-9]{1,3}|172\.(1[6-9]|2[0-9]|3[01])\.[0-9]{1,3}\.[0-9]{1,3})\b' "$file" | head -n 3
        ERRORS=$((ERRORS + 1))
    fi

    # Check generic credential patterns (API keys, OAuth tokens, private keys)
    if grep -E "(AIzaSy[A-Za-z0-9_-]{33}|ghp_[A-Za-z0-9]{36}|Bearer [A-Za-z0-9_\-\.]{20,}|-----BEGIN (RSA |EC |OPENSSH )?PRIVATE KEY-----)" "$file" > /dev/null; then
        echo "[FAIL][CREDENTIAL] '$rel_path' contains an API key or private key pattern!"
        ERRORS=$((ERRORS + 1))
    fi

    # Check hardcoded absolute user home directories
    if grep -E "/(home|Users)/[a-zA-Z0-9_\-]+/" "$file" > /dev/null; then
        echo "[FAIL][HOME-PATH] '$rel_path' contains a hardcoded home directory!"
        grep -En "/(home|Users)/[a-zA-Z0-9_\-]+/" "$file" | head -n 3
        ERRORS=$((ERRORS + 1))
    fi

done <<< "$FILES_TO_CHECK"

if [ "$ERRORS" -gt 0 ]; then
    echo "ZERO-PII AUDIT FAILED: $ERRORS issue(s) detected." >&2
    exit 1
else
    echo "ZERO-PII AUDIT PASSED: 0 private RFC 1918 IP, 0 credential, 0 home path found."
    exit 0
fi
