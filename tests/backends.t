Exercise every backend through the command-line interface.  basic.t covers the
full command surface against the default (text) backend; this file runs the
same core workflow against all three, so that breakage confined to a single
backend does not go unnoticed.

Set up environment

  $ . "${TESTDIR}/setup.sh"
  $ mkdir -p "${TMPDIR}/exports"

Import, look up, add, modify, remove and export, for each backend

  $ for backend in text json sqlite; do
  >   use_empty_backend "$backend"
  >   echo "== ${backend}"
  >   python3 -m ananke import "${EXAMPLE_DIR}/export.asc"
  >   python3 -m ananke lookup bazbank
  >   echo bazlibpass | python3 -m ananke add https://www.bazlib.org/ -i quux137 > /dev/null
  >   python3 -m ananke lookup bazlib
  >   echo quuxpass | python3 -m ananke modify -d https://www.bazlib.org/ -p > /dev/null
  >   python3 -m ananke lookup bazlib
  >   python3 -m ananke remove -d https://www.bazlib.org/
  >   python3 -m ananke lookup bazlib
  >   echo "lookup after remove: $?"
  >   python3 -m ananke export "${TMPDIR}/exports/${backend}.asc"
  >   python3 -m ananke configure -l | grep backend
  > done
  == text
  AnotherSecretPassword
  bazlibpass
  quuxpass
  lookup after remove: 1
  backend = text
  == json
  AnotherSecretPassword
  bazlibpass
  quuxpass
  lookup after remove: 1
  backend = json
  == sqlite
  AnotherSecretPassword
  bazlibpass
  quuxpass
  lookup after remove: 1
  backend = sqlite

A target must match a description exactly, and must match exactly one entry

  $ use_backend json
  $ python3 -m ananke remove -d bazbank
  Error: No entries match bazbank
  [1]

  $ python3 -m ananke remove -d https://www.foomail.com
  Error: Multiple entries match https://www.foomail.com
  [1]

  $ python3 -m ananke lookup www | wc -l
  \s*4 (re)

A missing configuration file is not an error, so long as the environment
supplies what it would have

  $ (unset ANANKE_BACKEND; rm -rf "${TMPDIR}/nocfg"; mkdir -p "${TMPDIR}/nocfg";
  >  ANANKE_CONFIG_DIR="${TMPDIR}/nocfg" ANANKE_DATA_DIR="${TMPDIR}/nocfg" \
  >  python3 -m ananke lookup foomail)
  Error: backend is not set
  [1]

  $ (rm -rf "${TMPDIR}/nocfg"; mkdir -p "${TMPDIR}/nocfg";
  >  ANANKE_CONFIG_DIR="${TMPDIR}/nocfg" ANANKE_DATA_DIR="${TMPDIR}/nocfg" \
  >  ANANKE_BACKEND=json ANANKE_KEY_ID=371C136C \
  >  python3 -m ananke import "${EXAMPLE_DIR}/export.asc")

Every backend writes an export that every other backend can import

  $ for target in text json sqlite; do
  >   for source in text json sqlite; do
  >     use_empty_backend "$target"
  >     python3 -m ananke import "${TMPDIR}/exports/${source}.asc"
  >     echo "${source} -> ${target}: $(python3 -m ananke lookup bazbank)"
  >   done
  > done
  text -> text: AnotherSecretPassword
  json -> text: AnotherSecretPassword
  sqlite -> text: AnotherSecretPassword
  text -> json: AnotherSecretPassword
  json -> json: AnotherSecretPassword
  sqlite -> json: AnotherSecretPassword
  text -> sqlite: AnotherSecretPassword
  json -> sqlite: AnotherSecretPassword
  sqlite -> sqlite: AnotherSecretPassword

# Local Variables:
# mode: prog
# tab-width: 2
# eval: (whitespace-mode 0)
# End:
