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
          (final: prev: {
              nextpnr = prev.nextpnr.overrideAttrs {
                version = "0e66c0ce";
                src = prev.fetchFromGitHub {
                  owner = "mole99";
                  repo = "nextpnr";
                  rev = "0e66c0ce4577d2668be1bdd60cb349da70577c01";
                  hash = "sha256-9KPClUbB/MbrgO8DPKW9J/gYoWkWnTWHNKqfue5cJaM=";
                  fetchSubmodules = true;
                };
                cmakeFlags =
                [
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
                version = "f3c81241";
                src = prev.fetchGitHubSnapshot {
                  owner = "mole99";
                  repo = "yosys";
                  rev = "f3c8124182f7a2f835674c1f1697f8ca16fbacb4";
                  hash = "sha256-y4HqpUfZKDNHn6/DYeU1M84niGH7RofgB7TmbT7Eu7c=";
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
        in
        {
          default = pkgs.mkShell {
            buildInputs = [ pkgs.nextpnr pkgs.yosys ];
          };
        }
      );
    };
}
