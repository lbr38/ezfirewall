<?php
$nftablesController = new \Controllers\Nftables();

/**
 * An IP address is required
 */
if (empty($_GET['ip'])) {
    throw new Exception('IP parameter is required');
}

/**
 * Validate the IP address format
 */
if (!filter_var($_GET['ip'], FILTER_VALIDATE_IP)) {
    throw new Exception('Invalid IP address format');
}

/**
 * Get the sanitized IP address
 */
$ip = $_GET['ip'];

/**
 * Get the top 10 destination port that have been blocked
 */
$topBlockedPorts = $nftablesController->getTopTenDestinationPorts(null, $ip);

unset($nftablesController);
