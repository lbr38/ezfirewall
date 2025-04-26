

**Define source IP addresses**

```shell
vim /opt/ezfirewall/sources/known_ips.yml
```

```yaml
---
# home
home_public: 1.2.3.4
home_lan: 192.168.0.0/24

# work
office_public: 5.6.7.8
```

**Define rulesets**

```shell
vim /opt/ezfirewall/rules/eth0.yml
```


```yaml
---
# The network interface name (use 'any' to apply to all interfaces)
eth0:
  # The IP version of the interface (v4 or v6)
  ip_version: 4

  # The input rules
  input:
    # The rule description name
    ssh:
      # The protocol (tcp or udp or icmp) (use 'any' to apply to both tcp and udp)
      protocol: tcp

      # The port(s) (use 'any' to apply to all ports) (no need to specify the ports for icmp)
      ports:
        - 22

      # The source(s) name or IP addresses to allow
      allow:
        - office_public
        # It can also be a CIDR range
        - 12.34.0.0/16

      # The source(s) name or IP addresses to reject
      drop:
        - x.x.x.x

  # The output rules
  output:
    # TODO
    
```

**Apply rules (launch the script)**

Must be run as root.

```shell
ezfirewall
```

**Check the rules**

```shell
nft list ruleset
```
