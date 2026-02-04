<?php
use Controllers\Utils\Generate\Html\Color;

$nftablesIpController = new \Controllers\Nftables\Ip();
$datasets = [];
$labels = [];
$options = [];

// A port is required
if (empty($_GET['port'])) {
    throw new Exception('Port parameter is required');
}

// Validate the port number format
if (!is_numeric($_GET['port']) || $_GET['port'] < 1 || $_GET['port'] > 65535) {
    throw new Exception('Invalid port number format');
}

// Get the sanitized port number
$port = $_GET['port'];

// Get the top 10 destination ips that have been blocked
$topBlockedIpsTcp = $nftablesIpController->getTopTenBlockedIpByPort($port, 'TCP');

foreach ($topBlockedIpsTcp as $myIp) {
    $labels[] = $myIp['Source_ip'];
    $datasets[0]['data'][] = $myIp['Count'];
    $datasets[0]['colors'][] = Color::random();
}

unset($nftablesIpController, $topBlockedIpsTcp, $myIp);
