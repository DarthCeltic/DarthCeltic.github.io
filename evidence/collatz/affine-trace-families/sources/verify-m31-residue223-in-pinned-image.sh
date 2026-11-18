#!/bin/sh
set -eu
cd /mathcase/project

if [ ! -f /mathcase/project/.lake/packages/mathlib/.lake/build/lib/lean/Mathlib/Data/Nat/Prime/Basic.olean ]; then
  echo "PINNED_MATHLIB_OLEAN_MISSING"
  exit 23
fi
printf '%s  %s\n' \
  '8a53e1cee2436efc347c6ebb07da0203d9c613670ad52bafdd0d0d19258d408c' \
  '/mathcase/input/CollatzAffineTrace.lean' \
  'a58a57ded7be3934f2cf96f1fe310dccb2eeea435b764d17a76fa4d8a9f73bd2' \
  '/mathcase/input/M31Residue223.lean' | sha256sum --check --status

version=$(lean --version)
case "$version" in
  *'version 4.33.1'*) ;;
  *) echo "UNEXPECTED_LEAN_VERSION: $version"; exit 24 ;;
esac
printf 'LEAN_VERSION=%s\n' "$version"

out_dir=/tmp/mathcase-m31-residue223
mkdir -p "$out_dir"
lean_paths="$out_dir:/mathcase/input:/mathcase/project/.lake/build/lib/lean"
for package in /mathcase/project/.lake/packages/*; do
  if [ -d "$package/.lake/build/lib/lean" ]; then
    lean_paths="$lean_paths:$package/.lake/build/lib/lean"
  fi
done
lean_prefix=$(lean --print-prefix)
LEAN_PATH="$lean_paths:$lean_prefix/lib/lean${LEAN_PATH:+:$LEAN_PATH}"
export LEAN_PATH

printf 'TRACE_HELPER_COMPILE_BEGIN\n'
lean --root=/mathcase/input -o "$out_dir/CollatzAffineTrace.olean" /mathcase/input/CollatzAffineTrace.lean
printf 'TRACE_HELPER_COMPILE_PASS\n'
printf 'M31_RESIDUE_223_COMPILE_BEGIN\n'
lean --root=/mathcase/input /mathcase/input/M31Residue223.lean
printf 'M31_RESIDUE_223_COMPILE_PASS\n'