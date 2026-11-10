#!/bin/bash
#
# Functional tests of ezfirewall, run by the CI after the package installation
# Rules are really applied: the container must be started with the NET_ADMIN capability
# (the container has its own network namespace, the runner ruleset is never modified)
#

set -euo pipefail

FIXTURES="$(cd "$(dirname "$0")/../fixtures" && pwd)"
EZFIREWALL="python3 /opt/ezfirewall/ezfirewall.py"
RULES_DIR="/opt/ezfirewall/rules"
SOURCES_DIR="/opt/ezfirewall/sources"
BACKUP_DIR="/opt/ezfirewall/backups"
NFTABLES_CONF="/etc/nftables.conf"

step() {
    echo
    echo "=================================================================="
    echo " $1"
    echo "=================================================================="
}

fail() {
    echo "FAIL: $1" >&2
    exit 1
}

# Current ruleset without the counters values (they change with the traffic)
ruleset() {
    nft list ruleset | sed -E 's/counter packets [0-9]+ bytes [0-9]+/counter/'
}

assert_contains() {
    local content="$1" expected="$2" description="$3"
    if ! grep -qE -- "$expected" <<< "$content"; then
        echo "$content"
        fail "$description (expected to match: $expected)"
    fi
    echo "OK: $description"
}

assert_not_contains() {
    local content="$1" unexpected="$2" description="$3"
    if grep -qE -- "$unexpected" <<< "$content"; then
        echo "$content"
        fail "$description (not expected to match: $unexpected)"
    fi
    echo "OK: $description"
}

step "Environment"
python3 --version
nft --version
nft list ruleset > /dev/null || fail "nftables cannot be used, is the container started with --cap-add=NET_ADMIN?"

# CI containers come with iptables-nft rules (docker embedded DNS) that nftables cannot re-create after a
# restore (xtables expressions, see the README), start from an empty ruleset so that the restore test is deterministic
nft flush ruleset

# Initial state, used to check the restore at the end
INITIAL_RULESET="$(ruleset)"
INITIAL_CONF_SUM="$(sha256sum "$NFTABLES_CONF" 2>/dev/null | cut -d' ' -f1 || true)"

step "Install the test fixtures"
mkdir -p "$RULES_DIR" "$SOURCES_DIR"
cp "$FIXTURES/config.yml" /opt/ezfirewall/config.yml
cp "$FIXTURES"/sources/*.yml "$SOURCES_DIR/"
cp "$FIXTURES"/rules/*.yml "$RULES_DIR/"

step "List sources"
OUTPUT="$($EZFIREWALL --list-sources)"
assert_contains "$OUTPUT" "bad_ip.*203\.0\.113\.66" "sources are listed"

step "Invalid rules are rejected"
declare -A INVALID_CASES=(
    ["unknown-parameter.yml"]='unknown parameter "prots"'
    ["duplicate-key.yml"]='duplicate key "ssh"'
    ["ip-version-mismatch.yml"]='cannot be used in an ipv4 section'
    ["drop-any.yml"]='"any" cannot be used in a drop list'
)

for file in "${!INVALID_CASES[@]}"; do
    cp "$FIXTURES/invalid/$file" "$RULES_DIR/zz-invalid.yml"

    if OUTPUT="$($EZFIREWALL --dry-run 2>&1)"; then
        echo "$OUTPUT"
        fail "$file was accepted"
    fi

    assert_contains "$OUTPUT" "${INVALID_CASES[$file]}" "$file is rejected with an explicit error"
    rm -f "$RULES_DIR/zz-invalid.yml"
done

[ "$(ruleset)" == "$INITIAL_RULESET" ] || fail "ruleset was modified by a rejected run"

step "Dry run"
$EZFIREWALL --dry-run
[ "$(ruleset)" == "$INITIAL_RULESET" ] || fail "ruleset was modified by a dry run"
echo "OK: ruleset unchanged after a dry run"

step "Apply rules"
$EZFIREWALL --quiet
APPLIED_RULESET="$(ruleset)"
echo "$APPLIED_RULESET"

# Tables and default policies
assert_contains "$APPLIED_RULESET" "table ip filter" "IPv4 filter table"
assert_contains "$APPLIED_RULESET" "table ip6 filter" "IPv6 filter table"
assert_contains "$APPLIED_RULESET" "table ip nat" "IPv4 NAT table"
assert_contains "$APPLIED_RULESET" "hook input priority [a-z0-9]+; policy drop;" "input default policy"
assert_contains "$APPLIED_RULESET" "hook output priority [a-z0-9]+; policy drop;" "IPv4 output default policy"
assert_contains "$APPLIED_RULESET" "hook forward priority [a-z0-9]+; policy drop;" "forward default policy"

# Input rules (merged from eth0.yml and admins.yml)
assert_contains "$APPLIED_RULESET" "set ez_in_eth0_ssh_drop" "input drop set"
assert_contains "$APPLIED_RULESET" "203\.0\.113\.66" "input drop set content"
assert_contains "$APPLIED_RULESET" "ip saddr 198\.51\.100\.10 tcp dport \{ 22, 2222 \}" "input rules merged from several files"
assert_contains "$APPLIED_RULESET" "ip saddr 192\.168\.100\.0/24 tcp dport \{ 22, 2222 \}" "input allow rule with a CIDR source"
assert_contains "$APPLIED_RULESET" "ip6 saddr 2001:db8:100::/64 tcp dport 22" "IPv6 input allow rule"
assert_contains "$APPLIED_RULESET" "set ez_in_any_dns_drop" "input drop set on any interface"
assert_contains "$APPLIED_RULESET" "IPv4 inbound denied" "dropped inbound packets are logged"

# Output rules
assert_contains "$APPLIED_RULESET" "oifname \"eth0\" ip daddr 9\.9\.9\.9 udp dport 53" "output allow rule"
assert_contains "$APPLIED_RULESET" "set ez_out_any_malicious_drop" "output drop set"
assert_contains "$APPLIED_RULESET" "IPv4 outbound denied" "dropped outbound packets are logged"
assert_contains "$APPLIED_RULESET" "oifname \"lo\" accept" "loopback output traffic is allowed"

# Forward and NAT rules
assert_contains "$APPLIED_RULESET" "iifname \"br0\" oifname \"eth0\"" "forward rule"
assert_contains "$APPLIED_RULESET" "FW-LAN-WAN" "forward rule log prefix"
assert_contains "$APPLIED_RULESET" "dnat to 192\.168\.100\.10" "DNAT rule"
assert_contains "$APPLIED_RULESET" "masquerade" "masquerade rule"

step "Persistence in $NFTABLES_CONF"
CONF="$(cat "$NFTABLES_CONF")"
assert_contains "$CONF" "Generated by ezfirewall" "configuration file generated"
assert_contains "$CONF" "^flush ruleset" "configuration file flushes the ruleset first"
nft -c -f "$NFTABLES_CONF" || fail "$NFTABLES_CONF cannot be loaded"
echo "OK: $NFTABLES_CONF is valid"

# Simulate a reboot: load the persisted file on an empty ruleset
nft flush ruleset
nft -f "$NFTABLES_CONF"
[ "$(ruleset)" == "$APPLIED_RULESET" ] || { diff <(echo "$APPLIED_RULESET") <(ruleset) || true; fail "persisted ruleset differs from the applied one"; }
echo "OK: persisted ruleset is identical to the applied one"

# Loading the file twice must not duplicate the rules
nft -f "$NFTABLES_CONF"
[ "$(ruleset)" == "$APPLIED_RULESET" ] || fail "loading $NFTABLES_CONF twice duplicates the rules"
echo "OK: $NFTABLES_CONF can be loaded several times"

step "Apply rules again (idempotence)"
$EZFIREWALL --quiet
[ "$(ruleset)" == "$APPLIED_RULESET" ] || { diff <(echo "$APPLIED_RULESET") <(ruleset) || true; fail "applying the same rules twice gives a different ruleset"; }
echo "OK: same ruleset after a second run"

step "Print rules"
OUTPUT="$($EZFIREWALL --print)"
echo "$OUTPUT"
assert_contains "$OUTPUT" "203\.0\.113\.66 \(bad_ip\)" "drop set content is printed with the source name"
assert_contains "$OUTPUT" "Chain .*OUTPUT" "output chain is printed"
assert_contains "$OUTPUT" "dnat to 192\.168\.100\.10 \(web_server\)" "NAT rule is printed with the source name"

step "Restore the initial backup"
# The oldest backup was made by the first apply, before any rule was applied
FIRST_BACKUP="$(ls -tr "$BACKUP_DIR"/*_ruleset.json | head -n 1)"
BACKUP_COUNT="$(ls "$BACKUP_DIR"/*_ruleset.json | wc -l)"
[ "$BACKUP_COUNT" -eq 2 ] || fail "expected 2 backups (one per apply), found $BACKUP_COUNT"
echo "OK: one backup per apply, none overwritten"

$EZFIREWALL --quiet --restore "$(basename "$FIRST_BACKUP")"
[ "$(ruleset)" == "$INITIAL_RULESET" ] || { diff <(echo "$INITIAL_RULESET") <(ruleset) || true; fail "initial ruleset was not restored"; }
echo "OK: initial ruleset restored"

if [ -n "$INITIAL_CONF_SUM" ]; then
    [ "$(sha256sum "$NFTABLES_CONF" | cut -d' ' -f1)" == "$INITIAL_CONF_SUM" ] || fail "$NFTABLES_CONF was not restored"
    echo "OK: $NFTABLES_CONF restored"
fi

step "Restore the most recent backup"
# The restore has made a backup of the applied ruleset, restoring the most recent backup undoes the restore
$EZFIREWALL --quiet --restore
[ "$(ruleset)" == "$APPLIED_RULESET" ] || { diff <(echo "$APPLIED_RULESET") <(ruleset) || true; fail "most recent backup was not restored"; }
echo "OK: most recent backup restored"

echo
echo "All tests passed"
