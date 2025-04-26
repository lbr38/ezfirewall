<?php
$nftablesControllers = new \Controllers\Nftables();
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
$firstDate = $nftablesControllers->getFirstDate();

/**
 * Get the last date of the logs in the database
 */
$lastDate = $nftablesControllers->getLastDate();

/**
 * Get the most blocked IP since first date
 */
$mostBlockedIP = $nftablesControllers->getMostBlockedIP();

/**
 * Get the most blocked port since first date
 */
$mostBlockedPort = $nftablesControllers->getMostBlockedPort();

/**
 * Get the top 10 destination port that have been blocked
 */
$topDestinationPorts = $nftablesControllers->getTopTenDestinationPorts($date);

/**
 * Get the top 10 IP address that have been blocked
 */
$topBlockedIPs = $nftablesControllers->getTopTenBlockedIPs($date);

