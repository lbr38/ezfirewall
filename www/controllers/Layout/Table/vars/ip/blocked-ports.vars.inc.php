<?php
$nftablesController = new \Controllers\Nftables();
$reloadableTableOffset = 0;

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
 *  Retrieve offset from cookie if exists
 */
if (!empty($_COOKIE['tables/ip/blocked-ports/offset']) and is_numeric($_COOKIE['tables/ip/blocked-ports/offset'])) {
    $reloadableTableOffset = $_COOKIE['tables/ip/blocked-ports/offset'];
}

/**
 *  Get list of blocked ports, with offset
 */
$reloadableTableContent = $nftablesController->getBlockedPort($ip, true, $reloadableTableOffset);

/**
 *  Get list of ALL bloeck ports, without offset, for the total count
 */
$reloadableTableTotalItems = count($nftablesController->getBlockedPort($ip));

/**
 *  Count total pages for the pagination
 */
$reloadableTableTotalPages = ceil($reloadableTableTotalItems / 10);

/**
 *  Calculate current page number
 */
$reloadableTableCurrentPage = ceil($reloadableTableOffset / 10) + 1;

unset($nftablesController);
