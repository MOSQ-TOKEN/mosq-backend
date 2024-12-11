{ pkgs ? import <nixpkgs> {} }:

pkgs.mkShell {
  buildInputs = [
    pkgs.glibc
    pkgs.python3
    pkgs.python3Packages.pip
  ];
}
