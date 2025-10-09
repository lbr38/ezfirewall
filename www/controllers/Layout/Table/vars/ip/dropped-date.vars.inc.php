<?php
$nftablesIpController = new \Controllers\Nftables\Ip();
$reloadableTableOffset = 0;
ini_set('memory_limit', '256M');

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
if (!empty($_COOKIE['tables/ip/dropped-date/offset']) and is_numeric($_COOKIE['tables/ip/dropped-date/offset'])) {
    $reloadableTableOffset = $_COOKIE['tables/ip/dropped-date/offset'];
}

/**
 *  Get list of dropped IPs, with offset
 */
$reloadableTableContent = $nftablesIpController->getDrop($ip, true, $reloadableTableOffset);

/**
 *  Get total count of dropped IPs
 */
$reloadableTableTotalItems = $nftablesIpController->getDrop($ip, false, 0, true)[0]['Count'];

/**
 *  Count total pages for the pagination
 */
$reloadableTableTotalPages = ceil($reloadableTableTotalItems / 10);

/**
 *  Calculate current page number
 */
$reloadableTableCurrentPage = ceil($reloadableTableOffset / 10) + 1;

unset($nftablesIpController);
