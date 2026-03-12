{
  nixConfig = {
    extra-substituters = [
      "https://nix-cache.fossi-foundation.org"
    ];
    extra-trusted-public-keys = [
      "nix-cache.fossi-foundation.org:3+K59iFwXqKsL7BNu6Guy0v+uTlwsxYQxjspXzqLYQs="
    ];
  };

  inputs = {
    nix-eda.url = "github:fossi-foundation/nix-eda/6.0.2";
    flake-utils.url = "github:numtide/flake-utils";
    flake-compat.url = "https://flakehub.com/f/edolstra/flake-compat/1.tar.gz";
  };

  outputs =
    {
      self,
      nix-eda,
      flake-utils,
      flake-compat,
    }:
    let
      nixpkgs = nix-eda.inputs.nixpkgs;
      lib = nixpkgs.lib;
    in
    {
      # Common
      overlays = {
        default = lib.composeManyExtensions [
          (nix-eda.composePythonOverlay (
            pkgs': pkgs: pypkgs': pypkgs:
            let
              callPythonPackage = lib.callPackageWith (pkgs' // pkgs'.python3.pkgs);
            in
            {
              fasm = callPythonPackage ./fasm.nix { };
            }
          ))
          (final: prev: {
            nextpnr = prev.nextpnr.overrideAttrs {
              version = "87f8f83b";
              src = prev.fetchFromGitHub {
                owner = "mole99";
                repo = "nextpnr";
                rev = "87f8f83ba44a380ca502a726dbaf7040a12931ab";
                hash = "sha256-7QCpZI6Pje92howE/x0fHguaQLefM1VQJma1RMXgXzw=";
                fetchSubmodules = true;
              };
              cmakeFlags = [
                "-DCURRENT_GIT_VERSION=nextpnr-0e66c0ce"
                "-DARCH=generic"
                "-DBUILD_TESTS=ON"
                "-DUSE_OPENMP=ON"
                # `Compatibility with CMake < 3.5 has been removed from CMake.`
                "-DCMAKE_POLICY_VERSION_MINIMUM=3.5"
              ];
            };
          })
          (final: prev: {
            yosys = prev.yosys.overrideAttrs {
              version = "774d9ba3";
              src = prev.fetchGitHubSnapshot {
                owner = "mole99";
                repo = "yosys";
                rev = "774d9ba3109f5b338d8724309cbf96941eb966b3";
                hash = "sha256-cLpKgDzCq1zDFSbFqcbgu2nGOUMMBGr0BCKk1/KUFJ4=";
                add-gitcommit = true;
              };
            };
          })
        ];
      };

      # Packages
      legacyPackages = nix-eda.forAllSystems (
        system:
        import nix-eda.inputs.nixpkgs {
          inherit system;
          overlays = [
            nix-eda.overlays.default
            self.overlays.default
          ];
        }
      );

      # Development Shells
      devShells = nix-eda.forAllSystems (
        system:
        let
          pkgs = self.legacyPackages."${system}";
          callPackage = lib.callPackageWith pkgs;
          python-env = (pkgs.python3.withPackages (ps: with ps; [ pkgs.python3.pkgs.fasm ]));
        in
        {
          default = pkgs.mkShell {
            buildInputs = [
              pkgs.nextpnr
              pkgs.yosys
              python-env
            ];
          };
        }
      );
    };
}
