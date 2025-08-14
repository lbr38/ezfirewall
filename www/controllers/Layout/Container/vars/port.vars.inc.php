<?php
/**
 * A port is required
 */
if (empty($_GET['port'])) {
    throw new Exception('Port parameter is required');
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
