<?php
$nftablesIpController = new \Controllers\Nftables\Ip();
$data = [];
$labels = [];

/**
 * A port is required
 */
if (empty($_GET['port'])) {
    throw new Exception('Port parameter is required');
}

/**
 * Validate the port number format
 */
if (!is_numeric($_GET['port']) || $_GET['port'] < 1 || $_GET['port'] > 65535) {
    throw new Exception('Invalid port number format');
}

/**
 * Get the sanitized port number
 */
$port = $_GET['port'];

/**
 * Get the top 10 destination ips that have been blocked
 */
$topBlockedIpsTcp = $nftablesIpController->getTopTenBlockedIpByPort($port, 'TCP');

/**
 * Prepare chart data
 */
$title = '';
$backgrounds = \Controllers\Layout\Color::randomColor(10);
foreach ($topBlockedIpsTcp as $myIp) {
    $labels[] = $myIp['Source_ip'];
    $data[] = $myIp['Count'];
}

unset($nftablesIpController, $topBlockedIpsTcp, $myIp);
