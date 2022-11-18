# @userboxd
A script that selects a random userbox from Wikipedia and posts it to Twitter. The script may be run periodically by a service or standalone.

## Service setup
This repo provides a NixOS service that will post userboxes every two hours.

1.  Write an `.env` file with your credentials in this directory with your credentials:  

    ```
    OAUTH_CONSUMER_KEY=twitter API key
    OAUTH_CONSUMER_SECRET=twitter API secret
    OAUTH_ACCESS_TOKEN=token from OAuth login
    OAUTH_ACCESS_SECRET=secret from OAuth login
    MASTODON_ACCESS_TOKEN=access token from mastodon application
    ```

2.  Import the module.  

    *Usage with flakes*
    ```nix
    {
        inputs = {
            userboxd.url = "github:wishdir/userboxd";
        };

        output = { self, userboxd }: {
            nixosConfigurations."..." = nixpkgs.lib.nixosSystem {
                modules = [
                    userboxd.nixosModule
                ];
            };
        };
    }
    ```

    *Usage in normal configuration*
    ```nix
    { config, ... }:

    {
        imports = [
            (import (builtins.fetchTarball "https://github.com/wishdir/userboxd/archive/refs/heads/main.tar.gz")).nixosModule
        ];
    }
    ```

    If you are not on NixOS, please make sure that these particular dependencies are installed and available to the script:
    - Python 3
    - Selenium (and associated Python module)
    - Chrome/Chromium ≥98

    Python packages needed:
    - Tweepy
    - Mastodon.py
    - Pillow

    Please also make sure that `chrome_bin_name` in the script is set to the correct name of the Chrome binary. This is dependent on platform, and is currently set to the name of the binary on NixOS.

    Twitter v1.1 API access is currently required for this script, As of this time, there is no way to post media via the v2 API at the time of writing.

3.  Configure the model in your system configuration:

    ```nix
    { config, ... }:

    {
        services.userboxd = {
            enable = true;
            envFilePath = "/path/to/.env";
            user = "user to run under";
        };
    }
    ```
