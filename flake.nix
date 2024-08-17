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

  outputs =
    {
      self,
      nixpkgs,
      flake-utils,
      ...
    }:
    let
      makeAnanke =
        pkgs:
        pkgs.python3Packages.buildPythonApplication {
          name = "ananke-py";
          pyproject = true;
          build-system = with pkgs.python3Packages; [ setuptools ];
          nativeCheckInputs = with pkgs.python3Packages; [
            cram
            mypy
            pkgs.gnupg
          ];
          src = builtins.path {
            path = ./.;
            name = "ananke-py-src";
          };
          patchPhase = "patchShebangs build.sh";
          preConfigure = "./build.sh generate -g ${self.shortRev or self.dirtyShortRev}";
          checkPhase = ''
            ./build.sh check
            ./build.sh test
          '';
        };
    in
    flake-utils.lib.eachDefaultSystem (
      system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
      in
      {
        packages.ananke = makeAnanke pkgs;
        packages.default = self.packages.${system}.ananke;
      }
    );
}
