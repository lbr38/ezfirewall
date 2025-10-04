<?php
$nftablesIpController = new \Controllers\Nftables\Ip();
$reloadableTableOffset = 0;

/**
 * A port is required
 */
if (empty($_GET['port'])) {
    throw new Exception('IP parameter is required');
}

/**
 * Validate the port number format
 */
if (!is_numeric($_GET['port']) || $_GET['port'] < 1 || $_GET['port'] > 65535) {
    throw new Exception('Invalid port number format');
}

/**
 * Get the sanitized port number
 */
$port = $_GET['port'];

/**
 *  Retrieve offset from cookie if exists
 */
if (!empty($_COOKIE['tables/port/blocked-ips/offset']) and is_numeric($_COOKIE['tables/port/blocked-ips/offset'])) {
    $reloadableTableOffset = $_COOKIE['tables/port/blocked-ips/offset'];
}

/**
 *  Get list of dropped ips, with offset
 */
$reloadableTableContent = $nftablesIpController->getBlockedIpByPort($port, true, $reloadableTableOffset);

/**
 *  Get list of ALL dropped ips, without offset, for the total count
 */
$reloadableTableTotalItems = count($nftablesIpController->getBlockedIpByPort($port));

/**
 *  Count total pages for the pagination
 */
$reloadableTableTotalPages = ceil($reloadableTableTotalItems / 10);

/**
 *  Calculate current page number
 */
$reloadableTableCurrentPage = ceil($reloadableTableOffset / 10) + 1;

unset($nftablesIpController);
