<?php
$nftablesController = new \Controllers\Nftables\Nftables();
$nftablesIpController = new \Controllers\Nftables\Ip();
$nftablesPortController = new \Controllers\Nftables\Port();
$date = date('Y-m-d');

if (!empty($_GET['date'])) {
    $date = $_GET['date'];
}

/**
 * Get the first date of the logs in the database
 */
$firstDate = $nftablesController->getFirstDate();

/**
 * Get the most blocked IP since first date
 */
$mostBlockedIP = $nftablesIpController->getMostBlockedIP();

/**
 * Get the most blocked port since first date
 */
$mostBlockedPort = $nftablesPortController->getMostBlockedPort();

unset($nftablesController, $nftablesIpController, $nftablesPortController);
