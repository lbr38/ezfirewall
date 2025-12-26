<?php
$nftablesIpController = new \Controllers\Nftables\Ip();
$reloadableTableOffset = 0;
ini_set('memory_limit', '256M');

/**
 *  Retrieve offset from cookie if exists
 */
if (!empty($_COOKIE['tables/home/dropped-ips-date/offset']) and is_numeric($_COOKIE['tables/home/dropped-ips-date/offset'])) {
    $reloadableTableOffset = $_COOKIE['tables/home/dropped-ips-date/offset'];
}

/**
 *  Get list of dropped IPs, with offset
 */
$reloadableTableContent = $nftablesIpController->getDrop('', true, $reloadableTableOffset);

/**
 *  Get total count of dropped IPs
 */
$reloadableTableTotalItems = $nftablesIpController->getDrop('', false, 0, true)[0]['Count'];

/**
 *  Count total pages for the pagination
 */
$reloadableTableTotalPages = ceil($reloadableTableTotalItems / 10);

/**
 *  Calculate current page number
 */
$reloadableTableCurrentPage = ceil($reloadableTableOffset / 10) + 1;

unset($nftablesIpController);
