<?php
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

/**
 * Get the top 10 destination port that have been blocked
 */
$topDestinationPorts = $nftablesPortController->getTopTenDestinationPorts($date);

/**
 * Prepare chart data
 */
$options['title']['text'] = 'Top 10 destination ports blocked on ' . strtolower($dateTitle);
$datasets[0]['backgroundColor'] = \Controllers\Layout\Color::randomColor(10);
foreach ($topDestinationPorts as $port) {
    $labels[] = $port['Dest_port'] . ' (' . $port['Protocol'] . ')';
    $datasets[0]['data'][] = $port['Count'];
}

unset($nftablesPortController, $topDestinationPorts, $port);
