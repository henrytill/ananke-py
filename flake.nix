{
  description = "A password manager";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixpkgs-unstable";
    flake-utils.url = "github:numtide/flake-utils";
    flake-compat = {
      url = "github:edolstra/flake-compat";
      flake = false;
    };
  };

  outputs = { self, nixpkgs, flake-utils, ... }:
    let
      makeAnanke = system:
        { }:
        let pkgs = nixpkgs.legacyPackages.${system};
        in pkgs.python3Packages.buildPythonApplication {
          name = "ananke";
          pname = "ananke";
          format = "pyproject";
          buildInputs = with pkgs.python3Packages; [ setuptools ];
          nativeCheckInputs = with pkgs; [ python3Packages.unittestCheckHook python3Packages.cram gnupg ];
          src = builtins.path {
            path = ./.;
            name = "ananke-py-src";
          };
          preConfigure = "make GIT_REF=${self.shortRev or self.dirtyShortRev} generate";
        };
    in flake-utils.lib.eachDefaultSystem (system:
      let ananke = makeAnanke system;
      in {
        packages.ananke = ananke { };
        packages.default = self.packages.${system}.ananke;
      });
}
