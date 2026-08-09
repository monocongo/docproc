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
was_enabled=0
if sudo pfctl -s info | grep -q 'Status: Enabled'; then
  was_enabled=1
fi

cleanup() {
  sudo pfctl -a "$anchor" -F all >/dev/null 2>&1 || true
  if [ "$was_enabled" -eq 0 ]; then
    sudo pfctl -d >/dev/null 2>&1 || true
  fi
}
trap cleanup EXIT HUP INT TERM

# macOS's stock /etc/pf.conf invokes the com.apple/* anchor. Refuse to claim
# enforcement when that hook is absent; loading an unreferenced PF anchor has
# no effect.
if ! sudo pfctl -sr | grep -Fq 'anchor "com.apple/*"'; then
  echo "network-deny-pf: /etc/pf.conf does not invoke com.apple/*; refusing unenforced run" >&2
  exit 2
fi

cat <<'RULES' | sudo pfctl -a "$anchor" -f -
# Permit only localhost traffic required by host Ollama and localhost-published
# MinIO/OpenSearch. All external IPv4 and IPv6 egress is denied.
pass out quick on lo0 all
block drop out quick inet from any to any
block drop out quick inet6 from any to any
RULES
sudo pfctl -E >/dev/null

# Prove that the anchor is loaded before starting the measured command. The
# caller must retain this output and separately record the expected failed
# external-denial probe as a harness-preflight observation.
sudo pfctl -a "$anchor" -sr
"$@"
