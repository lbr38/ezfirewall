<?php
$nftablesIpController = new \Controllers\Nftables\Ip();
$reloadableTableOffset = 0;

/**
 *  Retrieve offset from cookie if exists
 */
if (!empty($_COOKIE['tables/charts/blocked-ips/offset']) and is_numeric($_COOKIE['tables/charts/blocked-ips/offset'])) {
    $reloadableTableOffset = $_COOKIE['tables/charts/blocked-ips/offset'];
}

/**
 *  Get list of blocked IPs, with offset
 */
$reloadableTableContent = $nftablesIpController->getBlockedIP(true, $reloadableTableOffset);

/**
 *  Get list of ALL bloecked IPs, without offset, for the total count
 */
$reloadableTableTotalItems = count($nftablesIpController->getBlockedIP());

/**
 *  Count total pages for the pagination
 */
$reloadableTableTotalPages = ceil($reloadableTableTotalItems / 10);

/**
 *  Calculate current page number
 */
$reloadableTableCurrentPage = ceil($reloadableTableOffset / 10) + 1;

unset($nftablesIpController);
