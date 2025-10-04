<?php
// Read ezfirewall config file
if (is_readable(CONFIG)) {
    $yaml = yaml_parse_file(CONFIG);

    // Get config values
    $logRetention = $yaml['log_retention_days'] ?? null;
    $ipv4DefaultInputPolicy = $yaml['ipv4']['input_default_policy'] ?? null;
    $ipv6DefaultInputPolicy = $yaml['ipv6']['input_default_policy'] ?? null;
    $ipv4LogdroppedTraffic = $yaml['ipv4']['log_dropped_traffic'] ?? null;
    $ipv6LogdroppedTraffic = $yaml['ipv6']['log_dropped_traffic'] ?? null;
}
