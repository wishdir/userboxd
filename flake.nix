{
  description = "userboxd flake; provides package + service";

  inputs = {
    flake-compat = {
      url = "github:edolstra/flake-compat";
      flake = false;
    };

    nixpkgs.url = "github:NixOS/nixpkgs/nixos-21.11";
  };

  outputs = { self, nixpkgs, ... }:
    let
      pkgs = nixpkgs.legacyPackages.x86_64-linux;

      pythonWithDeps = pkgs.python39.withPackages
        (pypkgs: (with pypkgs; [
          tweepy
          mastodon-py
          pillow
          selenium
        ]));

      runtimeDeps = with pkgs; [
        google-chrome
        chromedriver
      ];
      runtimeDepsPath = nixpkgs.lib.makeBinPath runtimeDeps;

      userboxd = pkgs.writeShellScriptBin "userboxd" ''
        PATH=${runtimeDepsPath} ${pythonWithDeps}/bin/python3 ${./wikiarchive.py}
      '';
    in
    {
      packages."x86_64-linux" = { inherit userboxd; };
      defaultPackage."x86_64-linux" = userboxd;

      devShells."x86_64-linux".default = pkgs.mkShell {
        packages = [ pythonWithDeps ] ++ runtimeDeps;
      };

      nixosModules.default = { config, ... }: with nixpkgs.lib; {
        options.services.userboxd =
          {
            enable = mkEnableOption "Enable userboxd service";
            envFilePath = mkOption { type = types.str; };
            user = mkOption { type = types.str; };
          };

        config = let cfg = config.services.userboxd; in mkIf cfg.enable {
          systemd.services.userboxd-post = {
            serviceConfig = {
              Type = "oneshot";
              User = cfg.user;
              EnvironmentFile = cfg.envFilePath;
            };
            script = "${userboxd}/bin/userboxd";
          };

          systemd.timers.userboxd-post = {
            wantedBy = [ "timers.target" ];
            partOf = [ "userboxd-post.service" ];
            timerConfig = {
              OnCalendar = "0/2:00:00"; # every two hours
              Unit = "userboxd-post.service";
            };
          };
        };
      };
    };
}
