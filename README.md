# @userboxd
A script that selects a random userbox from Wikipedia and posts it to Twitter.

```
userboxd
├── .env (credentials)
├── userboxd.nix (NixOS expression)
└── wikiarchive.py (actual script)
```

The script may be run periodically by a service or standalone.

## General setup
Fairly straightforward on NixOS; simply create a `.env` in this directory with your credentials:  

`.env`
```
OAUTH_CONSUMER_KEY="twitter API key"
OAUTH_CONSUMER_SECRET="twitter API secret"
OAUTH_ACCESS_TOKEN="token from OAuth login"
OAUTH_ACCESS_SECRET="secret from OAuth login"
```

Dependencies are specified as part of a `nix-shell` shebang at the top of `wikiarchive.py`, and will be automatically brought in at execution time in NixOS.

If you are not on NixOS, please make sure that these particular dependencies are installed and available to the script:
- Python 3
- Selenium (and associated Python module)
- Chrome/Chromium ≥98
- Tweepy
- Pillow

Please also make sure that `chrome_bin_name` in the script is set to the correct name of the Chrome binary. This is dependent on platform, and is currently set to the name of the binary on NixOS.

Twitter v1.1 API access is currently required for this script, as there is no way to post media via the v2 API at the time of writing.

## Service setup on NixOS
Bring `userboxd.nix` into your imports:  

`configuration.nix`
```
{ config, ... }:

{
    imports = [
        /path/to/repo/userboxd.nix
    ];
    ...
}
```

Make sure the repo contains a `.env` populated with credentials.