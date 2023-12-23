{pkgs}: {
  deps = [
    pkgs.nix-update
    pkgs.nix
    pkgs.gitFull
    pkgs.imagemagick
    pkgs.libxcrypt
  ];
  env = {
    PYTHON_LD_LIBRARY_PATH = pkgs.lib.makeLibraryPath [
      pkgs.nix-update
      pkgs.nix
      pkgs.gitFull
      pkgs.libxcrypt
    ];
  };
}
