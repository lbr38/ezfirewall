<?php
$nftablesController = new \Controllers\Nftables\Nftables();
$datasets = [];
$labels = [];
$options = [];

// Prepare chart data
$options['title']['text'] = '';
$options['legend']['display'] = false;

// For dates between 15 days ago and today
$dateCounter = date('Y-m-d', strtotime('-' . $days . ' days'));

// Loop until today (+1 day to include today)
while (strtotime($dateCounter) <= strtotime(date('Y-m-d'))) {
    // Get drop count for that day and add it to the datasets
    $labels[] = $dateCounter;
    $datasets[0]['data'][] = $nftablesController->countByDate($dateCounter);

    // Move to the next day
    $dateCounter = date('Y-m-d', strtotime($dateCounter . ' +1 day'));
}

unset($nftablesController);
