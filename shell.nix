{ pkgs ? import <nixpkgs> {} }:

let
  tksvg = pkgs.python3Packages.buildPythonPackage rec {
    pname = "tksvg";
    version = "0.7.4";
    format = "setuptools";

    src = pkgs.fetchPypi {
      inherit pname version;
      sha256 = "e451c4301814306547afca80680e6db0cc6720b7d6cc3dca56beb17c2b29c0f5";
    };

    nativeBuildInputs = with pkgs; [
      cmake
      ninja
      python3Packages.scikit-build
      python3Packages.setuptools
      python3Packages.wheel
    ];

    buildInputs = with pkgs; [
      tcl
      tk
      libX11
    ];

    # scikit-build runs cmake; skip stdenv's cmake configure
    dontUseCmakeConfigure = true;

    # Upstream CMakeLists still declares cmake_minimum_required(2.8)
    env.CMAKE_ARGS = "-DCMAKE_POLICY_VERSION_MINIMUM=3.5";

    propagatedBuildInputs = [ pkgs.python3Packages.tkinter ];

    # Needs a display / live Tk for tests
    doCheck = false;

    pythonImportsCheck = [ "tksvg" ];
  };

  pythonEnv = pkgs.python3.withPackages (ps: [
    ps.tkinter
    ps.pillow
    tksvg
  ]);

  tclMinor = pkgs.lib.versions.majorMinor pkgs.tcl.version;
  tkMinor = pkgs.lib.versions.majorMinor pkgs.tk.version;
in
pkgs.mkShell {
  packages = [
    pythonEnv
    pkgs.tcl
    pkgs.tk
  ];

  shellHook = ''
    export TCL_LIBRARY="${pkgs.tcl}/lib/tcl${tclMinor}"
    export TK_LIBRARY="${pkgs.tk}/lib/tk${tkMinor}"
  '';
}
