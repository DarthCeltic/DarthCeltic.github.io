#!/bin/sh
set -eu

cd /mathcase/project
if [ ! -f /mathcase/project/.lake/packages/mathlib/.lake/build/lib/lean/Mathlib/Data/Nat/Prime/Basic.olean ]; then
  echo "PINNED_MATHLIB_OLEAN_MISSING"
  exit 23
fi

printf '%s  %s\n' \
  '8a53e1cee2436efc347c6ebb07da0203d9c613670ad52bafdd0d0d19258d408c' \
  '/mathcase/input/CollatzAffineTrace.lean' | sha256sum --check --status
printf '%s  %s\n' \
  'c75c33d7bc0d2cdc900a48c0ba062a657e5b8d7cd443e7166f09a25fbeb81004' \
  '/mathcase/input/M31Residue111.lean' | sha256sum --check --status

version=$(lean --version)
case "$version" in
  *'version 4.33.1'*) ;;
  *) echo "UNEXPECTED_LEAN_VERSION: $version"; exit 24 ;;
esac
printf 'LEAN_VERSION=%s\n' "$version"

out_dir=/tmp/mathcase-collatz-affine-trace
mkdir -p "$out_dir"
printf 'TRACE_HELPER_COMPILE_BEGIN\n'
lake env sh -c 'LEAN_PATH="/tmp/mathcase-collatz-affine-trace:/mathcase/input:$LEAN_PATH" lean --root=/mathcase/input -o /tmp/mathcase-collatz-affine-trace/CollatzAffineTrace.olean /mathcase/input/CollatzAffineTrace.lean'
printf 'TRACE_HELPER_COMPILE_PASS\n'
printf 'M31_UNIVERSAL_CERTIFICATE_COMPILE_BEGIN\n'
lake env sh -c 'LEAN_PATH="/tmp/mathcase-collatz-affine-trace:/mathcase/input:$LEAN_PATH" lean --root=/mathcase/input /mathcase/input/M31Residue111.lean'
printf 'M31_UNIVERSAL_CERTIFICATE_COMPILE_PASS\n'
