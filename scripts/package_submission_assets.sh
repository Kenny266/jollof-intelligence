#!/usr/bin/env bash
# scripts/package_submission_assets.sh
#
# Maintainer script: pack and fetch Ollama models + demo data bundles.
#
# Usage (called via Makefile targets from repo root):
#   bash scripts/package_submission_assets.sh pack-models
#   bash scripts/package_submission_assets.sh pack-demo-data
#   bash scripts/package_submission_assets.sh pack-all
#   bash scripts/package_submission_assets.sh fetch-models
#   bash scripts/package_submission_assets.sh fetch-demo-data
#
# Requires: curl, tar (both available in Git Bash on Windows)

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DIST_DIR="$REPO_ROOT/dist"
MODELS_DIR="$REPO_ROOT/backend/ollama_models"
DATA_DIR="$REPO_ROOT/backend/data"

# Load bundle URLs from root .env if present
ENV_FILE="$REPO_ROOT/.env"
if [[ -f "$ENV_FILE" ]]; then
  # shellcheck disable=SC1090
  set -a
  source "$ENV_FILE" 2>/dev/null || true
  set +a
fi

MODELS_BUNDLE_URL="${MODELS_BUNDLE_URL:-}"
DEMO_DATA_BUNDLE_URL="${DEMO_DATA_BUNDLE_URL:-}"

# ─── helpers ────────────────────────────────────────────────────────────────

log()  { echo "[package_submission_assets] $*"; }
ok()   { echo "[package_submission_assets] ✓ $*"; }
err()  { echo "[package_submission_assets] ✗ $*" >&2; exit 1; }

sha256sum_file() {
  local f="$1"
  if command -v sha256sum &>/dev/null; then
    sha256sum "$f"
  elif command -v shasum &>/dev/null; then
    shasum -a 256 "$f"
  else
    echo "(sha256sum not available)"
  fi
}

# ─── pack-models ─────────────────────────────────────────────────────────────

pack_models() {
  log "Packaging Ollama models..."

  for dir in generation judge embed; do
    local path="$MODELS_DIR/$dir"
    # Count non-.gitkeep files to check if models are actually present
    local count
    count=$(find "$path" -not -name ".gitkeep" -not -type d 2>/dev/null | wc -l || echo 0)
    if [[ "$count" -eq 0 ]]; then
      err "No model files found in $path — run 'make docker-up' first to pull models."
    fi
  done

  mkdir -p "$DIST_DIR"
  local out="$DIST_DIR/ollama_models.tar.gz"

  log "Creating $out ..."
  tar -czf "$out" \
    --exclude="*/.gitkeep" \
    -C "$REPO_ROOT/backend" \
    ollama_models/

  ok "Created $(du -sh "$out" | cut -f1) → $out"
  sha256sum_file "$out"
}

# ─── pack-demo-data ───────────────────────────────────────────────────────────

pack_demo_data() {
  log "Packaging demo data (SQLite + ChromaDB)..."

  local db="$DATA_DIR/jollof.db"
  local chroma="$DATA_DIR/chroma_db"

  [[ -f "$db" ]] || err "jollof.db not found at $db — run 'make pipeline' first."

  [[ -d "$chroma" ]] || err "chroma_db dir not found at $chroma — run 'make pipeline' first."

  local chroma_count
  chroma_count=$(find "$chroma" -type f 2>/dev/null | wc -l || echo 0)
  [[ "$chroma_count" -gt 0 ]] || err "chroma_db is empty — run 'make pipeline' first."

  mkdir -p "$DIST_DIR"
  local out="$DIST_DIR/demo_data.tar.gz"

  log "Creating $out ..."
  tar -czf "$out" \
    -C "$REPO_ROOT/backend" \
    data/jollof.db \
    data/chroma_db/

  ok "Created $(du -sh "$out" | cut -f1) → $out"
  sha256sum_file "$out"
}

# ─── pack-all ────────────────────────────────────────────────────────────────

pack_all() {
  pack_models
  pack_demo_data

  echo ""
  ok "Both bundles written to $DIST_DIR/"
  ls -lh "$DIST_DIR/"*.tar.gz 2>/dev/null || true
  echo ""
}

# ─── fetch-models ─────────────────────────────────────────────────────────────

fetch_models() {
  if [[ -z "$MODELS_BUNDLE_URL" ]]; then
    err "MODELS_BUNDLE_URL is not set. Set it in .env or pass it as an env var."
  fi

  # Skip if already populated
  local count
  count=$(find "$MODELS_DIR" -not -name ".gitkeep" -not -type d 2>/dev/null | wc -l || echo 0)
  if [[ "$count" -gt 0 ]]; then
    ok "Models already present in $MODELS_DIR — skipping download."
    return
  fi

  log "Downloading models from $MODELS_BUNDLE_URL ..."
  mkdir -p "$REPO_ROOT/backend"
  curl -L --ssl-no-revoke --progress-bar -o "$REPO_ROOT/backend/ollama_models.tar.gz" "$MODELS_BUNDLE_URL"

  log "Extracting to $REPO_ROOT/backend/ ..."
  tar -xzf "$REPO_ROOT/backend/ollama_models.tar.gz" -C "$REPO_ROOT/backend/"
  rm -f "$REPO_ROOT/backend/ollama_models.tar.gz"

  ok "Models extracted to $MODELS_DIR/"
}

# ─── fetch-demo-data ──────────────────────────────────────────────────────────

fetch_demo_data() {
  if [[ -z "$DEMO_DATA_BUNDLE_URL" ]]; then
    err "DEMO_DATA_BUNDLE_URL is not set. Set it in .env or pass it as an env var."
  fi

  # Skip if already present
  if [[ -f "$DATA_DIR/jollof.db" ]]; then
    ok "Demo data already present ($DATA_DIR/jollof.db) — skipping download."
    return
  fi

  log "Downloading demo data from $DEMO_DATA_BUNDLE_URL ..."
  mkdir -p "$DATA_DIR"
  curl -L --ssl-no-revoke --progress-bar -o "$DATA_DIR/demo_data.tar.gz" "$DEMO_DATA_BUNDLE_URL"

  log "Extracting to $REPO_ROOT/backend/ ..."
  tar -xzf "$DATA_DIR/demo_data.tar.gz" -C "$REPO_ROOT/backend/"
  rm -f "$DATA_DIR/demo_data.tar.gz"

  ok "Demo data extracted:"
  [[ -f "$DATA_DIR/jollof.db" ]] && ok "  jollof.db present" || err "  jollof.db missing after extract"
  [[ -d "$DATA_DIR/chroma_db" ]] && ok "  chroma_db present" || err "  chroma_db missing after extract"
}

# ─── dispatch ─────────────────────────────────────────────────────────────────

CMD="${1:-}"
case "$CMD" in
  pack-models)    pack_models ;;
  pack-demo-data) pack_demo_data ;;
  pack-all)       pack_all ;;
  fetch-models)   fetch_models ;;
  fetch-demo-data) fetch_demo_data ;;
  *)
    echo "Usage: $0 {pack-models|pack-demo-data|pack-all|fetch-models|fetch-demo-data}"
    exit 1
    ;;
esac
