<?php
$nftablesPortController = new \Controllers\Nftables\Port();
$datasets = [];
$labels = [];
$options = [];

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
$topBlockedPorts = $nftablesPortController->getTopTenDestinationPorts('', $ip);

/**
 * Prepare chart data
 */
$options['title']['text'] = '';
foreach ($topBlockedPorts as $myPort) {
    $labels[] = $myPort['Dest_port'];
    $datasets[0]['data'][] = $myPort['Count'];
}
$datasets[0]['backgroundColor'] = \Controllers\Layout\Color::randomColor(10);

unset($nftablesPortController, $topBlockedPorts, $myPort);
