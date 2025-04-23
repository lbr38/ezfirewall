

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
  input:
    # The rule description name
    ssh:
      # The port(s) (use 'any' to apply to all ports)
      port:
        - 22
      # The protocol(s) (use 'any' to apply to all protocols)
      protocols:
        - tcp
      # The source IP addresses to allow
      allow:
        - office_public

      # The source IP addresses to reject
      drop:
        - x.x.x.x
```
