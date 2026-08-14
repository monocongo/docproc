#!/bin/sh
# Refuse measured runs until a reviewed macOS network-isolation boundary exists.
#
# An anchor in an arbitrary host PF ruleset cannot prove egress denial: earlier
# anchors and existing/inbound-created state can bypass it, and a child can
# escape a shell-managed process group. Running a command would therefore make
# an unenforceable admission claim. This placeholder intentionally fails closed
# rather than loading or modifying PF rules.
set -eu

if [ "$(/usr/bin/uname -s)" != "Darwin" ]; then
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

echo "network-deny-pf: refusing run; an unmanaged host PF anchor cannot attest complete egress denial" >&2
echo "network-deny-pf: use a separately reviewed isolated guest or container network boundary" >&2
exit 2
