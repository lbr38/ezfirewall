<?php
$nftablesIpController = new \Controllers\Nftables\Ip();
$datasets = [];
$labels = [];
$options = [];

// An IP address is required
if (empty($_GET['ip'])) {
    throw new Exception('IP parameter is required');
}

// Validate the IP address format
if (!filter_var($_GET['ip'], FILTER_VALIDATE_IP)) {
    throw new Exception('Invalid IP address format');
}

// Get the sanitized IP address
$ip = $_GET['ip'];

// For dates between 15 days ago and today
$dateCounter = date('Y-m-d', strtotime('-15 days'));

// Loop until today (+1 day to include today)
while (strtotime($dateCounter) <= strtotime(date('Y-m-d'))) {
    // Get drop count for that day and add it to the dataset
    $labels[] = $dateCounter;
    $datasets[0]['data'][] = $nftablesIpController->countByDateIp($dateCounter, $ip);

    // Move to the next day
    $dateCounter = date('Y-m-d', strtotime($dateCounter . ' +1 day'));
}

unset($nftablesIpController);
