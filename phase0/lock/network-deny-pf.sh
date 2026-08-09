#!/bin/sh
# Run an already-prefetched Phase 0 command with macOS host egress blocked.
# This is intentionally a human-run command: it changes the packet filter and
# requires an administrator to review the rule before it is loaded.
set -eu

if [ "$(uname -s)" != "Darwin" ]; then
  echo "network-deny-pf: macOS PF is required" >&2
  exit 2
fi
if [ "$#" -eq 0 ]; then
  echo "usage: $0 -- command [argument ...]" >&2
  exit 2
fi
if [ "$1" = "--" ]; then
  shift
fi
if [ "$#" -eq 0 ]; then
  echo "network-deny-pf: missing command" >&2
  exit 2
fi

anchor="com.apple/docproc_phase0_$$"
rules_file=''
pf_token=''

cleanup() {
  [ -z "$rules_file" ] || rm -f "$rules_file"
  sudo pfctl -a "$anchor" -F all >/dev/null 2>&1 || true
  [ -z "$pf_token" ] || sudo pfctl -X "$pf_token" >/dev/null 2>&1 || true
}
trap cleanup EXIT HUP INT TERM

# macOS's stock /etc/pf.conf invokes the com.apple/* anchor. Refuse to claim
# enforcement when that hook is absent; loading an unreferenced PF anchor has
# no effect.
main_rules=$(sudo pfctl -sr) || {
  echo "network-deny-pf: could not inspect active PF rules" >&2
  exit 2
}
if ! printf '%s\n' "$main_rules" | grep -Fq 'anchor "com.apple/*"'; then
  echo "network-deny-pf: /etc/pf.conf does not invoke com.apple/*; refusing unenforced run" >&2
  exit 2
fi

rules_file=$(mktemp "${TMPDIR:-/tmp}/docproc-phase0-pf.XXXXXX") || exit 2
cat >"$rules_file" <<'RULES'
# Permit only localhost traffic required by host Ollama and localhost-published
# MinIO/OpenSearch. All external IPv4 and IPv6 egress is denied.
pass out quick on lo0 all
block drop out quick inet from any to any
block drop out quick inet6 from any to any
RULES
sudo pfctl -a "$anchor" -f "$rules_file"
rm -f "$rules_file"
rules_file=''
pf_enable=$(sudo pfctl -E) || {
  echo "network-deny-pf: could not enable PF" >&2
  exit 2
}
pf_token=$(printf '%s\n' "$pf_enable" | awk -F: '/Token/ {gsub(/[[:space:]]/, "", $NF); print $NF; exit}')
case "$pf_token" in
  ''|*[!0-9]*)
    echo "network-deny-pf: pfctl -E returned no usable PF reference token" >&2
    exit 2
    ;;
esac
printf '%s\n' "$pf_enable"

# Prove that the anchor is loaded and retain the main ruleset that reaches it
# before starting the measured command. The caller separately records the
# expected failed external-denial probe as a harness-preflight observation.
echo "network-deny-pf: active main ruleset"
printf '%s\n' "$main_rules"
echo "network-deny-pf: loaded anchor $anchor"
sudo pfctl -a "$anchor" -sr
"$@"
