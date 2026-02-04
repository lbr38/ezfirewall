<?php
use Controllers\Utils\Generate\Html\Color;

$nftablesPortController = new \Controllers\Nftables\Port();
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

// Get the top 10 destination port that have been blocked
$topDestinationPorts = $nftablesPortController->getTopTenDestinationPorts($date);

// Prepare chart data
$options['title']['text'] = 'Top 10 destination ports blocked on ' . strtolower($dateTitle);

// Populate data if results exist
foreach ($topDestinationPorts as $port) {
    $labels[] = $port['Dest_port'] . ' (' . $port['Protocol'] . ')';
    $datasets[0]['data'][] = $port['Count'];
    $datasets[0]['colors'][] = Color::random();
}

unset($nftablesPortController, $topDestinationPorts, $port);
