#!/usr/bin/env bash
# Download a large file in N parallel byte ranges (like a download manager), then join and size-check it.
# Usage: fetch_parallel.sh <url> <size_bytes> <out_file> [parts=8]
set -u
URL=$1; SIZE=$2; OUT=$3; N=${4:-8}
DIR="$OUT.parts"; mkdir -p "$DIR"
PART=$(( (SIZE + N - 1) / N ))
pids=()
for i in $(seq 0 $((N - 1))); do
  a=$((i * PART)); b=$(( (i + 1) * PART - 1 )); [ $b -ge $SIZE ] && b=$((SIZE - 1))
  want=$((b - a + 1))
  (
    f="$DIR/part$i"
    for try in $(seq 1 30); do
      have=$( [ -f "$f" ] && stat -c %s "$f" || echo 0 )
      [ "$have" -ge "$want" ] && exit 0
      curl -sL --max-time 900 -r $((a + have))-$b "$URL" >> "$f" || sleep 3
    done
    exit 1
  ) &
  pids+=($!)
done
fail=0
for p in "${pids[@]}"; do wait "$p" || fail=1; done
[ $fail = 0 ] || { echo "a part failed"; exit 1; }
cat $(for i in $(seq 0 $((N - 1))); do echo "$DIR/part$i"; done) > "$OUT"
got=$(stat -c %s "$OUT")
[ "$got" = "$SIZE" ] || { echo "size mismatch: $got vs $SIZE"; exit 1; }
rm -rf "$DIR"
echo "ok $OUT $got"
