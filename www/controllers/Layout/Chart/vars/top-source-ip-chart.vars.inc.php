<?php
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

/**
 *  Get the top 10 IP address that have been blocked
 */
$topBlockedIPs = $nftablesIpController->getTopTenBlockedIp($date);

/**
 *  Prepare chart data
 */
$options['title']['text'] = 'Top 10 IP addresses blocked on ' . strtolower($dateTitle);
$datasets[0]['backgroundColor'] = \Controllers\Layout\Color::randomColor(10);
foreach ($topBlockedIPs as $ip) {
    $labels[] =  $ip['Source_ip'];
    $datasets[0]['data'][] = $ip['Count'];
}

unset($nftablesIpController, $dateTitle, $topBlockedIPs, $ip);
