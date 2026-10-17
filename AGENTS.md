# AGENTS.md

This is the one instruction file. A `CLAUDE.md` symlink pointing here is a convenience some checkouts set up locally; it is not tracked, so a fresh clone has this file only.

## Project Overview

`ananke-py` is a Python port of [`ananke`](https://github.com/henrytill/ananke), a CLI password manager that
stores GPG-encrypted entries in one of three interchangeable storage backends. It is a work in progress and
explicitly not yet fit for general use.

## Development Commands

There is no task runner. The formatter, linter and type checkers run as [pre-commit](https://pre-commit.com) hooks,
declared in `flake.nix` with [git-hooks.nix](https://github.com/cachix/git-hooks.nix). Entering the dev shell
generates `.pre-commit-config.yaml` (a gitignored symlink into the Nix store; don't edit or commit it) and installs the
git hook.

```bash
nix develop                                # shell with the tools (gpg, cram, coverage included); installs the hook
pre-commit run --all-files                 # run the hooks over the whole repo by hand
python3 -m unittest discover -v -s tests   # unit tests (not a hook)
cram tests                                 # cram tests over tests/*.t (not a hook)
nix flake check -L                         # build and test the package, and run the hooks, in the sandbox
```

The hooks are nixfmt, ruff (lint, with `--fix`) and ruff-format on the changed files, and mypy and pyright on the
whole project, which both take what to check from `pyproject.toml`. They run against `typingEnv`, a Python with
`coverage`, because `tests/coverage_support/sitecustomize.py` imports it. CI (`.github/workflows/ci.yml`) runs
`nix flake check`, so it runs both the hooks (`checks.pre-commit`) and the tests (`checks.ananke`, the package's
check phase), the latter also against Python 3.12, the oldest `requires-python` admits (`checks.ananke-python312`).

Without Nix, `pip install -e '.[test,dev]'` installs the Python tools from PyPI to run by hand; there is no hook
configuration outside the dev shell.

Coverage, including the CLI runs the cram tests spawn (via `tests/coverage_support` on cram's `PYTHONPATH`):

```bash
rm -f .coverage .coverage.*
export COVERAGE_FILE=$PWD/.coverage COVERAGE_PROCESS_START=$PWD/pyproject.toml
python3 -m coverage run -m unittest discover -s tests
cram tests
python3 -m coverage combine && python3 -m coverage report
```

Running a single test:

```bash
python3 -m unittest tests.test_application            # one module
python3 -m unittest tests.test_data.TestEntry.test_x  # one test
cram tests/basic.t                                    # one cram file
```

### Version

Hatchling computes the version at build time by running `version.py`, which reads the base version from `VERSION`
and appends the git reference: `ANANKE_GIT_REF` if set (the flake sets it, since the sandbox has no `.git`),
otherwise `git rev-parse --short HEAD`. The result goes into the package metadata, and `ananke/__init__.py` reads
`__version__` from there with `importlib.metadata`, falling back to `unknown` when the package isn't installed. An
editable install records the version when it is made, not the current HEAD.

## Architecture

### Layering

`cli` → `application` → (`data`, `cipher`), with `config` feeding all of them. Nothing below `application`
knows about argparse; the CLI's `application()` function is the sole composition root.

### Startup sequence (`ananke/cli.py:application`)

Every command handler calls `application(OsFamily, os.environ)`, which:

1. Builds a `Config` via `ConfigBuilder().with_defaults(...).with_config().with_env(...)` — note the
   precedence: defaults, then the ini file, then environment variables win.
2. Creates `config_dir`, `data_dir`, `db_dir` with mode `0o700`.
3. Reads `data_dir/db/schema` (creating it at `CURRENT_SCHEMA_VERSION` if absent) and runs migrations when the
   on-disk version is older; raises if it is newer.
4. Instantiates the backend `Application` matching `config.backend`.

So changing config resolution or migration means touching `config.py`, `data/schema.py`, `data/migration.py`,
and this function together.

### Backends (`ananke/application/`)

All three implement the abstract `Application` (add / lookup / modify / remove / import_entries /
export_entries / clear) and are addressed by a `Target = EntryId | Description` union. The differences that
matter:

- `JsonApplication` and `SqliteApplication` hold `Entry` objects whose `ciphertext` is *binary* GPG output
  (`cipher.gpg.Binary`), base64-encoded for storage in `db/data.json` / `db/db.sqlite`.
- `TextApplication` uses ASCII-armored GPG (`cipher.gpg.Text`): an encrypted index of `SecureIndexElement`
  at `db/index.asc` plus one encrypted `SecureEntry` object file per entry under an objects directory.
- Regardless of backend, `import`/`export` always use the armored `SecureEntry` JSON format, which is why
  `example/export.asc` is loadable by every backend.

`application/common.py` holds the shared pieces:

- `Query`/`QueryMatcher` — case-insensitive substring matching on description and identity. This is the
  *search* path, used by `lookup`.
- `target_matches`/`find_one` — a `Target` matches a description by **equality**, and `modify`/`remove`
  require exactly one match, raising `NoEntries`/`MultipleEntries` (both `ValueError` subclasses) otherwise.
  This is the *addressing* path. Keep the two distinct: the reference implementation defines target
  matching this way, and mixing them in is what let SQLite's `remove` delete every match at once.
- The generic `read`/`write` helpers that (de)serialize `Dictable` lists through an optional cipher.

### Data model (`ananke/data/`)

- `Record` is the read side (entry_id, key_id, timestamp, description, identity, meta, plaintext);
  `Entry` is the stored, still-encrypted form and only yields plaintext after `with_cipher(...)` attaches a
  cipher. `SecureEntry`/`SecureIndexElement` are the armored-text counterparts.
- Newtypes (`Description`, `Identity`, `Metadata`, `KeyId`) and wrapper classes (`EntryId` over UUID,
  `Timestamp` over UTC datetime, `Plaintext`, `Ciphertext`) are used pervasively — pass the wrapper, not the
  bare `str`.
- JSON on disk is camelCase; Python is snake_case. `remap_keys_camel_to_snake` / `remap_keys_snake_to_camel`
  bridge the two and are applied in `application/common.read`/`write`.
- Schema is at version 4 (`data/schema.py`). Migrations are one-step-at-a-time functions chained in
  `migrate_json_data` / `migrate_sqlite_data`; the text backend has no migrations. Adding a version means
  bumping `CURRENT_SCHEMA_VERSION`, adding a `_migrate_*_vN_to_vN+1`, extending both chains, and adding a
  fixture under `tests/migration_data/`. `cli.migrate` records the new version once migration succeeds —
  without that write, migrations re-run on every invocation, which for JSON means re-assigning every
  entry id.

### Cipher (`ananke/cipher/`)

`Cipher[T]` is generic over the ciphertext representation; `gpg.Binary` is `Cipher[Ciphertext]` and `gpg.Text`
is `Cipher[ArmoredCiphertext]`. Both shell out to the `gpg` binary via `subprocess` with a 30s timeout and
raise `ValueError` on failure. `Binary.suggest_key()` is what `ananke configure` offers as a default key.

### Configuration

Ini file at `<config_dir>/ananke.ini` with `[data] backend, dir` and `[gpg] key_id, allow_multiple_keys`.
Env overrides: `ANANKE_CONFIG_DIR`, `ANANKE_DATA_DIR`, `ANANKE_BACKEND`, `ANANKE_KEY_ID`,
`ANANKE_ALLOW_MULTIPLE_KEYS`. Defaults follow XDG on POSIX and `APPDATA`/`LOCALAPPDATA` on NT (`OsFamily`),
so both paths need to keep working.

## Testing

`basic.t` covers the full command surface against the text backend; `backends.t` runs the core workflow
against all three and checks that each can import the others' exports. Backend-specific breakage is
invisible to the unit tests, which construct applications directly rather than through `cli.application()`.

Tests require the `gpg` binary. They point `GNUPGHOME` at the committed `example/gnupg` keyring (key id
`371C136C`) and import `example/export.asc` as fixture data; `tests/setup.sh` does this for cram, and
`test_gpg.py` / `test_application.py` do it in `setUp`. Unit tests generally run each backend against the
same test-case table in a `TemporaryDirectory`. `tests/test_doctest.py` pulls doctests out of
`ananke.data.common` into unittest discovery, so docstring examples there are executed.

## Code Style

Line length 120, enforced by ruff (format, plus lint rules E, W, F, I and PL; see `pyproject.toml` for the
ignores). mypy strict and pyright strict over `ananke`, `tests` and `version.py`. Python 3.12+ — the code uses PEP 695 syntax (`type X = ...`,
`class Cipher[T]`, `def read[T: Dictable]`) and `match` statements over the `Backend`/`OsFamily` enums; keep
those matches exhaustive rather than adding a default case. Packages re-export their public API through
`__init__.py` using explicit `X as X` aliases — add new public names there in the same form.
