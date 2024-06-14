Set up environment

  $ . "${TESTDIR}/setup.sh"

Print usage string

  $ python3 -m ananke
  usage: __main__.py [-h] [--version]
                     {add,lookup,modify,remove,import,export,configure} ...
  
  A minimal password manager.
  
  positional arguments:
    {add,lookup,modify,remove,import,export,configure}
                          Commands
      add                 add an entry
      lookup              lookup an entry
      modify              modify an entry
      remove              remove an entry
      import              import entries from JSON file
      export              export entries to JSON file
      configure           create, modify, and list configuration
  
  options:
    -h, --help            show this help message and exit
    --version             show program's version number and exit
  [2]

Import example data

  $ python3 -m ananke import "${EXAMPLE_DIR}/db/data.json"

  $ python3 -m ananke lookup foomail
  https://www.foomail.com quux ASecretPassword
  https://www.foomail.com altquux ThisIsMyAltPassword

  $ python3 -m ananke lookup bazbank
  AnotherSecretPassword

  $ python3 -m ananke lookup barphone
  YetAnotherSecretPassword

  $ python3 -m ananke lookup www
  https://www.foomail.com quux ASecretPassword
  https://www.bazbank.com quux AnotherSecretPassword
  https://www.barphone.com quux YetAnotherSecretPassword
  https://www.foomail.com altquux ThisIsMyAltPassword

Lookup non-existent entry and add it

  $ python3 -m ananke lookup bazlib
  [1]

  $ echo foopass | python3 -m ananke add https://www.bazlib.org/ -i quux137
  Enter plaintext:  (no-eol)

  $ python3 -m ananke lookup bazlib
  foopass

Modify

  $ echo quuxpass | python3 -m ananke modify -d https://www.bazlib.org/ -p
  Enter plaintext:  (no-eol)

  $ python3 -m ananke lookup bazlib
  quuxpass

Configure

  $ python3 -m ananke configure -l
  config_dir = /tmp/.+ (re)
  data_dir = /tmp/.+ (re)
  backend = json
  key_id = 371C136C
  allow_multiple_keys = False

# Local Variables:
# mode: prog
# tab-width: 2
# eval: (whitespace-mode 0)
# End:
