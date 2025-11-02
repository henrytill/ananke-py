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
      baseVersion = nixpkgs.lib.trim (builtins.readFile ./VERSION);
      gitRef = self.shortRev or self.dirtyShortRev;
      version = "${baseVersion}+${gitRef}";
      makeAnanke =
        pkgs:
        pkgs.python3Packages.buildPythonApplication {
          pname = "ananke-py";
          inherit version;
          pyproject = true;
          build-system = with pkgs.python3Packages; [ flit-core ];
          nativeCheckInputs = with pkgs.python3Packages; [
            cram
            mypy
            pkgs.gnupg
          ];
          src = self;
          patchPhase = "patchShebangs run.py";
          preConfigure = "./run.py generate -g ${gitRef}";
          checkPhase = ''
            ./run.py check
            ./run.py test
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
