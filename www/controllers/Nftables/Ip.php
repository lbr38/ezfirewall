<?php

namespace Controllers\Nftables;

class Ip extends Nftables
{
    protected $model;

    public function __construct()
    {
        parent::__construct();
        $this->model = new \Models\Nftables\Ip();
    }

    /**
     * Return all drops
     * It is possible to filter by IP address
     * It is possible to add an offset to the request
     * @return array
     */
    public function getDrop(string $ip = '', bool $withOffset = false, int $offset = 0, bool $count = false) : array
    {
        return $this->model->getDrop($ip, $withOffset, $offset, $count);
    }

    /**
     * Return all blocked IP
     * It is possible to add an offset to the request
     * @return array
     */
    public function getBlockedIP(bool $withOffset = false, int $offset = 0, bool $count = false) : array
    {
        return $this->model->getBlockedIP($withOffset, $offset, $count);
    }

    /**
     * Return the list of blocked IPs for a specific port
     * It is possible to add an offset to the request
     * @return array
     */
    public function getBlockedIpByPort(int $port, bool $withOffset = false, int $offset = 0) : array
    {
        return $this->model->getBlockedIpByPort($port, $withOffset, $offset);
    }

    /**
     * Return the top 10 IP address that have been blocked
     * @return array
     */
    public function getTopTenBlockedIp(string $date = '') : array
    {
        return $this->model->getTopTenBlockedIp($date);
    }

    /**
     * Return the top 10 IP address that have been blocked, by port and protocol (optional)
     * @return array
     */
    public function getTopTenBlockedIpByPort(int $port, string|null $protocol = null) : array
    {
        return $this->model->getTopTenBlockedIpByPort($port, $protocol);
    }

    /**
     * Return the most blocked IP
     * @return array
     */
    public function getMostBlockedIP() : array
    {
        return $this->model->getMostBlockedIP();
    }

    /**
     * Count the number of dropped packets for a specific date and IP
     * @param string $date
     * @param string $ip
     * @return int
     */
    public function countByDateIp(string $date, string $ip) : int
    {
        return $this->model->countByDateIp($date, $ip);
    }
}
