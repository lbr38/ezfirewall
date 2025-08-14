<?php
$nftablesPortController = new \Controllers\Nftables\Port();

/**
 * An IP address is required
 */
if (empty($_GET['ip'])) {
    throw new Exception('IP parameter is required');
}

/**
 * Validate the IP address format
 */
if (!filter_var($_GET['ip'], FILTER_VALIDATE_IP)) {
    throw new Exception('Invalid IP address format');
}

/**
 * Get the sanitized IP address
 */
$ip = $_GET['ip'];

/**
 * Get the top 10 destination port that have been blocked
 */
$topBlockedPorts = $nftablesPortController->getTopTenDestinationPorts(null, $ip);

/**
 * Prepare chart data
 */
$title = '';
$backgrounds = \Controllers\Layout\Color::randomColor(10);
foreach ($topBlockedPorts as $myPort) {
    $labels[] = $myPort['Dest_port'];
    $data[] = $myPort['Count'];
}

unset($nftablesPortController, $topBlockedPorts, $myPort);
