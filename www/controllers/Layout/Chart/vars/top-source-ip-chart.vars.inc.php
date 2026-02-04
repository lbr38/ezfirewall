<?php
use Controllers\Utils\Generate\Html\Color;

$nftablesIpController = new \Controllers\Nftables\Ip();
$date = date('Y-m-d');
$datasets = [];
$labels = [];
$options = [];

if (!empty($_GET['date'])) {
    $date = $_GET['date'];
}

if ($date == date('Y-m-d')) {
    $dateTitle = 'Today';
} else {
    $dateTitle = $date;
}

// Get the top 10 IP address that have been blocked
$topBlockedIPs = $nftablesIpController->getTopTenBlockedIp($date);

// Prepare chart data
$options['title']['text'] = 'Top 10 IP addresses blocked on ' . strtolower($dateTitle);

// Populate data if results exist
foreach ($topBlockedIPs as $ip) {
    $labels[] = $ip['Source_ip'];
    $datasets[0]['data'][] = $ip['Count'];
    $datasets[0]['colors'][] = Color::random();
}

unset($nftablesIpController, $dateTitle, $topBlockedIPs, $ip);
