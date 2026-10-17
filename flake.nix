{
  description = "A password manager";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixpkgs-unstable";
    flake-utils.url = "github:numtide/flake-utils";
    flake-compat = {
      url = "github:edolstra/flake-compat";
      flake = false;
    };
    git-hooks = {
      url = "github:cachix/git-hooks.nix";
      inputs.nixpkgs.follows = "nixpkgs";
      inputs.flake-compat.follows = "flake-compat";
    };
  };

  outputs =
    {
      self,
      nixpkgs,
      flake-utils,
      git-hooks,
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
          build-system = [ pkgs.python3Packages.hatchling ];
          nativeCheckInputs = with pkgs; [
            gnupg
            python3Packages.cram
          ];
          src = self;
          # version.py asks git for the reference, and the sandbox has no .git.
          env.ANANKE_GIT_REF = gitRef;
          checkPhase = ''
            runHook preCheck
            python3 -m unittest discover -v -s tests
            cram tests
            runHook postCheck
          '';
        };
    in
    flake-utils.lib.eachDefaultSystem (
      system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
        # The type checkers need to import coverage, which tests/coverage_support uses and the hooks' own tools don't
        # see otherwise.
        typingEnv = pkgs.python3.withPackages (ps: [
          ps.coverage
          ps.mypy
        ]);
        preCommit = git-hooks.lib.${system}.run {
          src = ./.;
          hooks = {
            nixfmt.enable = true;
            ruff.enable = true;
            ruff-format.enable = true;
            # The type checkers look at the whole project, not just the files that changed, so that a change to one
            # module is checked against the modules using it. Both take what to check from pyproject.toml.
            mypy = {
              enable = true;
              pass_filenames = false;
              package = typingEnv;
            };
            pyright = {
              enable = true;
              pass_filenames = false;
              entry = "${pkgs.pyright}/bin/pyright --pythonpath ${typingEnv}/bin/python";
            };
          };
        };
      in
      {
        packages.ananke = makeAnanke pkgs;
        packages.default = self.packages.${system}.ananke;

        # The package's check phase runs the tests.
        checks.ananke = self.packages.${system}.ananke;
        # Runs the hooks over the whole repo. They are kept out of the package's check phase so that a new release of
        # one of the tools fails `nix flake check` rather than the build.
        checks.pre-commit = preCommit;

        # The shellHook generates .pre-commit-config.yaml and installs the git hook.
        devShells.default = pkgs.mkShell {
          inputsFrom = [ self.packages.${system}.ananke ];
          packages = preCommit.enabledPackages ++ [
            pkgs.pre-commit
            pkgs.python3Packages.coverage
            pkgs.yaml-language-server
          ];
          inherit (preCommit) shellHook;
        };
      }
    );
}
