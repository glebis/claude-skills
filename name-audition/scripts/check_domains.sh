#!/usr/bin/env bash
# check_domains.sh — authoritative domain-availability check via WHOIS + DNS NS.
#
# Usage:
#   check_domains.sh NAME [NAME ...] [-- TLD ...]
#   check_domains.sh praxio dyad sessio
#   check_domains.sh praxio dyad -- com ai io
#   TLDS="com org ai" check_domains.sh praxio
#
# Defaults: TLDs = com org ai io app co  (override via -- args or $TLDS).
#
# Availability heuristic (authoritative for REGISTRATION, not trademark):
#   - WHOIS says "No match / NOT FOUND / Domain not found / No Data Found"
#     AND `dig +short NS` returns nothing  => AVAILABLE
#   - Creation Date / Registrar / NS present                => TAKEN
#   - Anything ambiguous (rate-limited, .ai flakiness, etc.) => UNKNOWN (verify by hand)
#
# WHOIS is authoritative for whether a domain is REGISTERED. It says nothing about
# trademarks. `.ai` whois is often rate-limited or terse — treat UNKNOWN as "check manually".

set -u

# --- parse args: names before `--`, TLDs after (or from $TLDS env) ---
NAMES=()
TLD_ARGS=()
after_sep=0
for arg in "$@"; do
  if [ "$arg" = "--" ]; then after_sep=1; continue; fi
  if [ "$after_sep" -eq 1 ]; then TLD_ARGS+=("$arg"); else NAMES+=("$arg"); fi
done

if [ "${#NAMES[@]}" -eq 0 ]; then
  echo "usage: check_domains.sh NAME [NAME ...] [-- TLD ...]" >&2
  exit 64
fi

if [ "${#TLD_ARGS[@]}" -gt 0 ]; then
  TLDS_LIST=("${TLD_ARGS[@]}")
elif [ -n "${TLDS:-}" ]; then
  # shellcheck disable=SC2206
  TLDS_LIST=(${TLDS})
else
  TLDS_LIST=(com org ai io app co)
fi

command -v whois >/dev/null 2>&1 || { echo "error: 'whois' not found" >&2; exit 69; }
command -v dig   >/dev/null 2>&1 || { echo "error: 'dig' not found"   >&2; exit 69; }

# Patterns that indicate "not registered" in WHOIS output across registries.
AVAIL_RE='no match|not found|no data found|no entries found|status: *available|domain not found|not been registered|no object found'
# Patterns that indicate "registered".
TAKEN_RE='creation date|registrar:|registry domain id|name server|nserver|domain status: *(active|ok|client)'

# Run whois and follow an IANA TLD referral if the bare query returned the
# registry-object instead of the domain record (common on macOS whois).
do_whois() {
  local domain="$1" out refer
  out="$(whois "$domain" 2>/dev/null)"
  # IANA referral object: contains "refer:" and a "domain: <TLD>" object, not our domain.
  if printf '%s' "$out" | grep -qi '^refer:' && \
     ! printf '%s' "$out" | grep -qi "domain name: *$domain"; then
    refer="$(printf '%s' "$out" | grep -i '^refer:' | head -n1 | awk '{print $2}')"
    if [ -n "$refer" ]; then
      out="$(whois -h "$refer" "$domain" 2>/dev/null)"
    fi
  fi
  printf '%s' "$out"
}

classify() {
  local domain="$1" who ns who_lc
  # NS lookup first (fast, authoritative signal of an active registration).
  ns="$(dig +short NS "$domain" 2>/dev/null | head -n1)"
  # WHOIS (follows IANA referral when needed).
  who="$(do_whois "$domain")"
  who_lc="$(printf '%s' "$who" | tr '[:upper:]' '[:lower:]')"

  local has_ns=0 says_avail=0 says_taken=0
  [ -n "$ns" ] && has_ns=1
  printf '%s' "$who_lc" | grep -Eq "$AVAIL_RE" && says_avail=1
  printf '%s' "$who_lc" | grep -Eq "$TAKEN_RE" && says_taken=1

  if [ "$has_ns" -eq 0 ] && [ "$says_avail" -eq 1 ] && [ "$says_taken" -eq 0 ]; then
    echo "AVAILABLE"
  elif [ "$has_ns" -eq 1 ] || [ "$says_taken" -eq 1 ]; then
    echo "TAKEN"
  else
    echo "UNKNOWN"
  fi
}

# --- header ---
printf '%-16s' "name"
for t in "${TLDS_LIST[@]}"; do printf '%-12s' ".$t"; done
printf '\n'
total_cols=$(( 16 + 12 * ${#TLDS_LIST[@]} ))
printf '%*s\n' "$total_cols" '' | tr ' ' '-'

# --- rows ---
for name in "${NAMES[@]}"; do
  lname="$(printf '%s' "$name" | tr '[:upper:]' '[:lower:]')"
  printf '%-16s' "$lname"
  for t in "${TLDS_LIST[@]}"; do
    domain="${lname}.${t}"
    status="$(classify "$domain")"
    case "$status" in
      AVAILABLE) printf '%-12s' "free" ;;
      TAKEN)     printf '%-12s' "taken" ;;
      *)         printf '%-12s' "?" ;;
    esac
  done
  printf '\n'
done

echo
echo "Legend: free = WHOIS no-match + no NS (registrable). taken = registered. ? = verify by hand (rate-limit / .ai flakiness)."
echo "NOTE: WHOIS is authoritative for REGISTRATION only — NOT for trademark. Always run a separate trademark check."
