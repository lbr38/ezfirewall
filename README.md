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
  --no-persist        : Do not save rules to /etc/nftables.conf
  --print, -p         : Print the rules currently in place
  --list-sources, -ls : List current sources
  --restore [file]    : Restore a backup of the ruleset (the most recent one if no file is specified)
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
        # The protocol (tcp, udp, icmp or any)
        # 'any' applies to all protocols, or to both tcp and udp when ports are specified
        # 'icmp' only matches ping requests (echo-request), ICMP packets related to existing connections are always accepted
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

    # The output rules (same syntax as the input rules, but 'allow' and 'drop' are the destinations
    # of the outbound packets, and the interface is the outbound interface)
    output:
      # Allow DNS queries to the trusted resolvers only
      dns:
        protocol: udp
        ports:
          - 53
        allow:
          - 9.9.9.9
          - 1.1.1.1

      # Block all outbound traffic to a malicious network
      malicious:
        protocol: any
        drop:
          - 10.66.0.0/16
```

By default, `output_default_policy` is `accept`: output rules are only useful to `drop` some destinations. Set `output_default_policy: drop` in the configuration file to only allow the outbound traffic explicitly defined in the output rules (established connections, loopback and IPv6 neighbor discovery are always allowed).

Advanced ruleset example (forward)
----------------------------------

This is an example of a forward ruleset. It allows traffic from the LAN to the WAN and blocks traffic from the guest network to the LAN.

```shell
vim /opt/ezfirewall/rules/eth0.yml
```

```yaml
---
eth0:
  ipv4:
    forward:
      lan_to_wan:
        action: accept
        log: true
        log_prefix: FW-LAN-WAN
        rules:
          - from_interface: br0
            to_interface: eth0
            from_source: home_lan
            protocol: tcp
            to_port: 443

          - from_interface: br0
            to_interface: eth0
            from_source: home_lan
            protocol: udp
            to_port: 53

      block_guest_to_lan:
        action: drop
        rules:
          - from_interface: br1
            to_interface: br0
            from_source: guest_lan

  ipv6:
    forward:
      allow_v6_dns:
        action: accept
        rules:
          - from_interface: br0
            to_interface: eth0
            from_source: 2001:db8:1::/64
            protocol: udp
            to_port: 53
```

Forward rule fields:

- `action` (optional): `accept` (default), `drop` or `reject`.
- `log` (optional): `true`/`false` (default `false`).
- `log_prefix` (optional): custom nftables log prefix.
- `rules` (required): list of match objects.
- Match object fields: `from_interface`, `to_interface`, `from_source`, `to_destination`, `protocol`, `from_port`, `to_port`. At least one of `from_interface` or `to_interface` is required, the other fields are optional.

Notes:

- `from_source` and `to_destination` can be either a source alias from `/opt/ezfirewall/sources/*.yml` or a direct IP/CIDR value.
- `protocol` can be `tcp`, `udp`, `icmp` or `any` (default). `any` means all protocols, or both `tcp` and `udp` when ports are specified.
- `from_port` and `to_port` can be a port or a list of ports, they can only be used when `protocol` is `tcp`, `udp` or `any`.
- Forwarded traffic that does not match any rule is handled by the `forward_default_policy` of the configuration file (`drop` by default). No final drop rule is added to the FORWARD chain, so that rules appended by other services (e.g. docker) keep working.

Advanced ruleset example (NAT)
------------------------------

This is an example of a NAT ruleset. It redirects the HTTP port of the public address to a server of the LAN (DNAT) and masquerades the traffic of the LAN going to the WAN (SNAT).

```shell
vim /opt/ezfirewall/rules/nat.yml
```

```yaml
---
eth0:
  ipv4:
    nat:
      prerouting:
        web_server:
          in_interface: eth0
          destination: office_public
          protocol: tcp
          to_port: 80
          to_destination: 192.168.0.10

      postrouting:
        lan_to_wan:
          out_interface: eth0
          source: home_lan
          masquerade: true

        # Alternatively, translate to a fixed address (SNAT)
        # lan_to_wan:
        #   out_interface: eth0
        #   source: home_lan
        #   to_source: 5.6.7.8
```

NAT rule fields:

- `prerouting` (DNAT) rules: `in_interface`, `destination`, `protocol`, `to_port` (all optional) and `to_destination` (required).
- `postrouting` (SNAT) rules: `out_interface`, `source`, `protocol` (all optional) and either `to_source` or `masquerade: true` (required).
- `protocol` can be `tcp`, `udp` or `any` (default). `any` means all protocols, or both `tcp` and `udp` when `to_port` is specified.
- `destination`, `to_destination`, `source` and `to_source` can be either a source alias from `/opt/ezfirewall/sources/*.yml` or a direct IP/CIDR value.

Rules validation and merging
----------------------------

All the rules files are checked before applying anything: an unknown parameter, an invalid protocol or port, or a key defined twice in the same file is reported as an error, so that a typo can never lead to a rule silently ignored or matching more traffic than expected.

Rules with the same name defined in several files (e.g. a `ssh` rule in `eth0.yml` and in `admins.yml`) are merged (sources and ports are combined), as long as they use the same protocol. Otherwise an error is displayed.

Apply the rules
---------------

Must be run as root.

```shell
ezfirewall
```

Check the rules
---------------

Print the rules currently in place as tables (one table per nftables table, the content of the drop sets and the source names are displayed):

```shell
ezfirewall --print
```

The raw ruleset can still be listed with the nftables native command:

```shell
nft list ruleset
```

Change default policies
-----------------------

Edit the `/opt/ezfirewall/config.yml` file and change the `input_default_policy` / `output_default_policy` / `forward_default_policy` values to `accept` or `drop`.

With a default policy set to `accept`, the traffic that does not match any rule is accepted (and not logged). Default values are `drop` for input and forward, `accept` for output.

If a parameter is missing from the configuration file, it is added with its default value.

Backups and restore
-------------------

Before applying the rules, the current ruleset and `/etc/nftables.conf` are saved to `/opt/ezfirewall/backups` (backups are kept 15 days). If something fails after the rules have been applied, the backup is automatically restored.

To manually restore a backup:

```shell
# Restore the most recent backup
ezfirewall --restore

# Restore a specific backup
ezfirewall --restore 2026-01-01_10-00-00_ruleset.json
```

Rules created by iptables-nft (e.g. by docker) using xtables extensions cannot be restored by nftables: restart the services that created them (the services listed in `restart_services` are restarted automatically after a restore).

Log dropped packets
-------------------

- rsyslog is required

Edit the `/opt/ezfirewall/config.yml` file and change the `log_dropped_traffic` value to `True` to log the dropped packets.

Only the inbound and outbound packets dropped by the default input/output policies are logged. Forwarded packets dropped by the default forward policy are not logged (use `log: true` on a forward rule to log a specific traffic).

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
  forward_default_policy: drop
  log_dropped_traffic: True
ipv6:
  input_default_policy: drop
  output_default_policy: accept
  forward_default_policy: drop
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
