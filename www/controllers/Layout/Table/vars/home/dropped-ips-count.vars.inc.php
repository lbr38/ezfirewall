<?php
$nftablesIpController = new \Controllers\Nftables\Ip();
$reloadableTableOffset = 0;

/**
 *  Retrieve offset from cookie if exists
 */
if (!empty($_COOKIE['tables/home/dropped-ips-count/offset']) and is_numeric($_COOKIE['tables/home/dropped-ips-count/offset'])) {
    $reloadableTableOffset = $_COOKIE['tables/home/dropped-ips-count/offset'];
}

/**
 *  Get list of dropped IPs, with offset
 */
$reloadableTableContent = $nftablesIpController->getBlockedIP(true, $reloadableTableOffset);

/**
 *  Get total count of dropped IPs
 */
$reloadableTableTotalItems = $nftablesIpController->getBlockedIP(false, 0, true)[0]['Count'];

/**
 *  Count total pages for the pagination
 */
$reloadableTableTotalPages = ceil($reloadableTableTotalItems / 10);

/**
 *  Calculate current page number
 */
$reloadableTableCurrentPage = ceil($reloadableTableOffset / 10) + 1;

unset($nftablesIpController);
