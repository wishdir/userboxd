{ pkgs, ... }:

{
  systemd.services.userboxd-post = {
    serviceConfig = {
      Type = "oneshot";
      EnvironmentFile = "${./.env}";
    };
    path = with pkgs; [ nix ];
    script = ". /etc/profile; ${./wikiarchive.py}";
  };

  systemd.timers.userboxd-post = {
    wantedBy = [ "timers.target" ];
    partOf = [ "userboxd-post.service" ];
    timerConfig = {
      OnCalendar = "0/2:00:00"; # every two hours
      Unit = "userboxd-post.service";
    };
  };
}
