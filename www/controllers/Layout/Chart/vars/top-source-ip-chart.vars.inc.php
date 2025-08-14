<?php
$nftablesIpController = new \Controllers\Nftables\Ip();
$date = date('Y-m-d');
$data = [];
$labels = [];

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
$title = 'Top 10 IP addresses blocked on ' . strtolower($dateTitle);
$backgrounds = \Controllers\Layout\Color::randomColor(10);

foreach ($topBlockedIPs as $ip) {
    $labels[] =  $ip['Source_ip'];
    $data[] = $ip['Count'];
}

unset($nftablesIpController, $dateTitle, $topBlockedIPs);
