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
was_enabled=0
pf_info=$(sudo pfctl -s info) || {
  echo "network-deny-pf: could not inspect PF status" >&2
  exit 2
}
if printf '%s\n' "$pf_info" | grep -q 'Status: Enabled'; then
  was_enabled=1
fi

cleanup() {
  [ -z "$rules_file" ] || rm -f "$rules_file"
  sudo pfctl -a "$anchor" -F all >/dev/null 2>&1 || true
  if [ "$was_enabled" -eq 0 ]; then
    sudo pfctl -d >/dev/null 2>&1 || true
  fi
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
sudo pfctl -E >/dev/null

# Prove that the anchor is loaded before starting the measured command. The
# caller must retain this output and separately record the expected failed
# external-denial probe as a harness-preflight observation.
sudo pfctl -a "$anchor" -sr
"$@"
