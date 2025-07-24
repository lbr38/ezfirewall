<?php
$nftablesController = new \Controllers\Nftables();
$date = date('Y-m-d');

if (!empty($_GET['date'])) {
    $date = $_GET['date'];
}

if ($date == date('Y-m-d')) {
    $dateTitle = 'Today';
} else {
    $dateTitle = $date;
}

/**
 * Get the first date of the logs in the database
 */
$firstDate = $nftablesController->getFirstDate();

/**
 * Get the last date of the logs in the database
 */
$lastDate = $nftablesController->getLastDate();

/**
 * Get the most blocked IP since first date
 */
$mostBlockedIP = $nftablesController->getMostBlockedIP();

/**
 * Get the most blocked port since first date
 */
$mostBlockedPort = $nftablesController->getMostBlockedPort();

/**
 * Get the top 10 destination port that have been blocked
 */
$topDestinationPorts = $nftablesController->getTopTenDestinationPorts($date);

/**
 * Get the top 10 IP address that have been blocked
 */
$topBlockedIPs = $nftablesController->getTopTenBlockedIPs($date);

unset($nftablesController);
