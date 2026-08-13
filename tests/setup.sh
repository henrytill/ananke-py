EXAMPLE_DIR="${TESTDIR}/../example"
export GNUPGHOME="${EXAMPLE_DIR}/gnupg"
export ANANKE_CONFIG_DIR=$TMPDIR
export ANANKE_DATA_DIR=$TMPDIR
export PYTHONPATH="${TESTDIR}/.."
cp "${EXAMPLE_DIR}/ananke.ini" $ANANKE_CONFIG_DIR

# Point the config and data directories at a backend-specific subdirectory, so
# that each backend runs against a store of its own.  The environment takes
# precedence over the copied ini file, which pins the text backend.
use_backend() {
  export ANANKE_BACKEND="$1"
  export ANANKE_CONFIG_DIR="${TMPDIR}/$1"
  export ANANKE_DATA_DIR="${TMPDIR}/$1"
  mkdir -p "$ANANKE_CONFIG_DIR"
  cp "${EXAMPLE_DIR}/ananke.ini" "$ANANKE_CONFIG_DIR"
}

# As use_backend, but discards any store left behind by a previous call.
use_empty_backend() {
  rm -rf "${TMPDIR}/$1"
  use_backend "$1"
}
