<?php
$nftablesPortController = new \Controllers\Nftables\Port();
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

// For dates between 15 days ago and today
$dateCounter = date('Y-m-d', strtotime('-15 days'));

// Loop until today (+1 day to include today)
while (strtotime($dateCounter) <= strtotime(date('Y-m-d'))) {
    // Get drop count for that day and add it to the dataset
    $labels[] = $dateCounter;
    $datasets[0]['data'][] = $nftablesPortController->countByDatePort($dateCounter, $port);

    // Move to the next day
    $dateCounter = date('Y-m-d', strtotime($dateCounter . ' +1 day'));
}

unset($nftablesPortController);
