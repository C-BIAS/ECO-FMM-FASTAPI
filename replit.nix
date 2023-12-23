{ pkgs }:
{
  deps = [
    pkgs.mailutils
    pkgs.gitFull
    pkgs.imagemagick
    pkgs.libxcrypt
  ];

  env = {
    PYTHON_LD_LIBRARY_PATH = pkgs.lib.makeLibraryPath [
      pkgs.gitFull
      pkgs.libxcrypt
    ];
  };
}