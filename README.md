Ezfirewall
==========

A python program to easily manage nftables firewall rules using YAML.

- Language: **Python 3.x**
- Backend: **nftables**
- IPv6 compatible
- Docker compatible

```
           __ _                        _ _ 
  ___ ____/ _(_)_ __ _____      ____ _| | |
 / _ \_  / |_| | '__/ _ \ \ /\ / / _` | | |
|  __// /|  _| | | |  __/\ V  V / (_| | | |
 \___/___|_| |_|_|  \___| \_/\_/ \__,_|_|_|
                                           
Available parameters:
  --help, -h          : Print this help
  --quiet, -q         : Enable quiet mode (answer yes to all questions)
  --debug             : Enable debug mode
  --dry-run, -d       : Enable dry run mode
  --list-sources, -ls : List current sources
```

Install
=======

<img src="https://github.com/user-attachments/assets/6bf74c2c-c8bc-4ffd-9fa4-ba1d89de0b27" width="18" /> **Debian 11/12, Ubuntu 22.04 and newer**

```shell
curl -sS https://packages.repomanager.net/repo/gpgkeys/packages.repomanager.net.pub | gpg --dearmor > /etc/apt/trusted.gpg.d/packages.repomanager.net.gpg
```

```shell
cat << EOF > /etc/apt/sources.list.d/ezfirewall.list
deb https://packages.repomanager.net/repo/deb/ezfirewall/debian/main/prod debian main
EOF
```

```shell
apt update
apt install ezfirewall
```

<img src="https://github.com/user-attachments/assets/f14deb0d-bf59-4147-844b-b8a2762f7f13" width="18" /> **RHEL 8 based OS (RedHat, CentOS, Alma...)**

```shell
cat << EOF > /etc/yum.repos.d/ezfirewall.repo
[ezfirewall]
name=ezfirewall repo on packages.repomanager.net
baseurl=https://packages.repomanager.net/repo/rpm/ezfirewall/8/prod
enabled=1
gpgkey=https://packages.repomanager.net/repo/gpgkeys/packages.repomanager.net.pub
gpgcheck=1
EOF
```

```shell
dnf install ezfirewall
```

<img src="https://github.com/user-attachments/assets/f14deb0d-bf59-4147-844b-b8a2762f7f13" width="18" /> **RHEL 9 based OS (RedHat, CentOS, Alma...)**

```shell
cat << EOF > /etc/yum.repos.d/ezfirewall.repo
[ezfirewall]
name=ezfirewall repo on packages.repomanager.net
baseurl=https://packages.repomanager.net/repo/rpm/ezfirewall/9/prod
enabled=1
gpgkey=https://packages.repomanager.net/repo/gpgkeys/packages.repomanager.net.pub
gpgcheck=1
EOF
```

```shell
dnf install ezfirewall
```

<img src="https://github.com/user-attachments/assets/f14deb0d-bf59-4147-844b-b8a2762f7f13" width="18" /> **RHEL 10 based OS (RedHat, CentOS, Alma...)**

```shell
cat << EOF > /etc/yum.repos.d/ezfirewall.repo
[ezfirewall]
name=ezfirewall repo on packages.repomanager.net
baseurl=https://packages.repomanager.net/repo/rpm/ezfirewall/10/prod
enabled=1
gpgkey=https://packages.repomanager.net/repo/gpgkeys/packages.repomanager.net.pub
gpgcheck=1
EOF
```

```shell
dnf install ezfirewall
```

How to
======

1. Define the IP adresses
2. Define rulesets
3. Apply

Define source IP addresses
--------------------------

Create YAML files with the IP you trust or want to block and give them a name. They can then be used in the rulesets. Example:

```shell
vim /opt/ezfirewall/sources/trusted_networks.yml
```

```yaml
---
# home
home_lan: 192.168.0.0/24

# work
office_public: 5.6.7.8
```

Define rulesets
---------------

Name your rulesets after the network interface they apply to easily identify them. For example `eth0.yml`.

```shell
vim /opt/ezfirewall/rules/eth0.yml
```

```yaml
---
# The network interface name (use 'any' to apply to all interfaces)
eth0:
  # The IP version of the interface (v4 or v6)
  ipv4:
    # The input rules
    input:
      # The rule description name
      ssh:
        # The protocol (tcp or udp or icmp) (use 'any' to apply to both tcp and udp)
        protocol: tcp

        # The port(s) (use 'any' to apply to all ports) (no need to specify the ports for icmp)
        ports:
          - 22

        # The source name(s) or IP addresses to allow
        allow:
          - home_lan
          - office_public
          # It can also be a CIDR range
          - 12.34.0.0/16

        # The source name(s) or IP addresses to reject
        drop:
          - malicious_ip
          - malicious_ip2
          - malicious_ip3
          - 1.2.3.4

    # The output rules
    # output:
    # TODO: for now output rules are not implemented, all output traffic is allowed
    
```

Apply the rules
---------------

Must be run as root.

```shell
ezfirewall
```

Check the rules
---------------

Use nftables native command to list the current rules. The output is horrible but I haven't found the time to create a better command yet.

```shell
nft list ruleset
```

Change default input/output policy
----------------------------------

Edit the `/opt/ezfirewall/config.yml` file and change the `input_default_policy` / `output_default_policy` values to `accept` or `drop`

Log dropped packets
-------------------

- rsyslog is required

Edit the `/opt/ezfirewall/config.yml` file and change the `log_dropped_traffic` value to `True` to log the dropped packets.

Raw logs are stored in `/var/log/nftables.log` and also in a dedicated database under `/var/lib/ezfirewall/ezfirewall.db` (database is used by the web interface).

`log_retention_days` defines how many days the logs are kept in the database (default is 30 days).

Restart services after applying the rules
-----------------------------------------

Edit the `/opt/ezfirewall/config.yml` file and edit the `restart_services` list to include the services you want to restart after applying the rules.

Example:

```yaml
ipv4:
  input_default_policy: drop
  output_default_policy: accept
  log_dropped_traffic: True
ipv6:
  input_default_policy: drop
  output_default_policy: accept
  log_dropped_traffic: True
log_retention_days: 30
restart_services: 
  - docker
```

Web interface
=============

A web interface is available to easily visualize the dropped traffic.

<div align="center">
    <img src="https://github.com/user-attachments/assets/b42d27e9-4d83-4245-b771-33aa1a094b6e">
    &nbsp;
    <img src="https://github.com/user-attachments/assets/20b3c3f2-66b3-46f3-baa2-7ee9492bce6c">
    &nbsp;
    <img src="https://github.com/user-attachments/assets/ec0801b2-a9f7-42e5-b28e-8e02790b1b41">
    &nbsp;
    <img src="https://github.com/user-attachments/assets/721aaaf7-2210-40d1-ad5f-3995cce2c828">
</div>
<br>

**Requirements to use the web interface**:

- Set the `log_dropped_traffic` options to `True` in the configuration file to enable logging of dropped packets.
- You will need a web server with PHP 8.2 or newer and PHP SQLite, Yaml extensions installed (`php8.x-sqlite3`, `php8.x-yaml` on Debian based OS).
- The web server must serve the files from `/opt/ezfirewall/www/public`.
- SSL certificate is recommended unless you are using it only on a local network.

Here is an example of a Nginx vhost configuration for the web interface:

```nginx

upstream php-handler {
    # PHP-FPM 8.2 socket for ezfirewall
    server unix:/run/php/ezfirewall-php8.2-fpm.sock;
}

# Disable useless logging
map $request_uri $loggable {
    /ajax/controller.php 0;
    default 1;
}

server {
    listen <SERVER-IP>:80;
    server_name <FQDN>;

    access_log /var/log/nginx/<FQDN>_access.log combined if=$loggable;
    error_log /var/log/nginx/<FQDN>_error.log;

    return 301 https://$server_name$request_uri;
}
 
server {
    set $ROOT_DIR '/opt/ezfirewall/www/public';

    listen <SERVER-IP>:443 ssl;
    server_name <FQDN>;

    # Path to SSL certificate/key files
    ssl_certificate <PATH_TO_CERTIFICATE>;
    ssl_certificate_key <PATH_TO_PRIVATE_KEY>;

    # Path to log files
    access_log /var/log/nginx/<FQDN>_ssl_access.log combined if=$loggable;
    error_log /var/log/nginx/<FQDN>_ssl_error.log;
 
    # Security headers
    add_header Strict-Transport-Security "max-age=15768000; includeSubDomains; preload;" always;
    add_header Referrer-Policy "no-referrer" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-Download-Options "noopen" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Permitted-Cross-Domain-Policies "none" always;
    add_header X-Robots-Tag "none" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # Remove X-Powered-By, which is an information leak
    fastcgi_hide_header X-Powered-By;

    # Path to root directory
    root $ROOT_DIR;
 
    location / {
        rewrite ^ /index.php;
    }

    # Reverse proxy for http://ip-api.com
    # Useful to serve http over https
    location /api/ip {
        proxy_pass http://ip-api.com/json;
        proxy_set_header Host ip-api.com;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    location ~ \.php$ {
        include fastcgi_params;
        fastcgi_param SCRIPT_FILENAME $request_filename;
        fastcgi_param HTTPS on;
        # Avoid sending the security headers twice
        fastcgi_param modHeadersAvailable true;
        fastcgi_pass php-handler;
        fastcgi_intercept_errors on;
        fastcgi_request_buffering off;
        fastcgi_read_timeout 120;
    }

    # Static files
    location ~ \.(svg|png|html|ttf|ico|jpg|jpeg|gif|css|js)$ {
        expires 7d;
        add_header Cache-Control "public, max-age=3600 immutable";
        access_log off;
    }
}
```
