#!/usr/bin/env bash
# Compile a byte-identical, source-SHA-pinned copy of the PRIVATE Agent v1.
# This is only a disposable contract fixture, never a deployable artifact.
set -euo pipefail
cd "$(dirname "$0")/.."
while read -r expected path; do
  [[ -z "${expected:-}" || "${expected:0:1}" == "#" ]] && continue
  observed="$(git hash-object "$path")"
  if [[ "$observed" != "$expected" ]]; then
    echo "ERROR: pinned Agent fixture modified without manifest update: $path" >&2
    exit 1
  fi
done < SOURCE_BLOBS.sha1
echo "Pinned Agent v1 fixture SHA: PASS"
mkdir -p build/product-v1-test lib
fetch_jar() {
  local name="$1" path="$2" tmp="$1.partial" root
  if [[ -s "$name" ]] && jar tf "$name" >/dev/null 2>&1; then return; fi
  rm -f "$name" "$tmp"
  for root in https://repo.maven.apache.org/maven2 https://repo1.maven.org/maven2; do
    if curl --silent --show-error --fail --location --retry 3 --retry-all-errors \
        --retry-delay 2 --connect-timeout 10 --max-time 90 \
        -o "$tmp" "$root/$path"; then
      if jar tf "$tmp" >/dev/null 2>&1; then mv "$tmp" "$name"; return; fi
    fi
    rm -f "$tmp"
  done
  echo "ERROR: could not download verified Java test dependency: $name" >&2
  exit 1
}
fetch_jar lib/sqlite-jdbc.jar "org/xerial/sqlite-jdbc/3.46.1.3/sqlite-jdbc-3.46.1.3.jar"
fetch_jar lib/slf4j-api.jar "org/slf4j/slf4j-api/2.0.16/slf4j-api-2.0.16.jar"
fetch_jar lib/slf4j-nop.jar "org/slf4j/slf4j-nop/2.0.16/slf4j-nop-2.0.16.jar"
javac --release 8 -encoding UTF-8 -d build/product-v1-test \
  src/main/java/net/neristal/rrbridge/product/v1/*.java \
  src/test/java/net/neristal/rrbridge/product/v1/ProductServerE2E.java
echo "Pinned Java8 Agent source compile: PASS"
