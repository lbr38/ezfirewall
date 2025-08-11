<?php

namespace Controllers\Nftables;

use Exception;

class Port extends Nftables
{
    protected $model;

    public function __construct()
    {
        parent::__construct();
        $this->model = new \Models\Nftables\Port();
    }

    /**
     * Return blocked port by ip
     * It is possible to add an offset to the request
     * @return array
     */
    public function getBlockedPortByIp(string $ip, bool $withOffset = false, int $offset = 0) : array
    {
        return $this->model->getBlockedPortByIp($ip, $withOffset, $offset);
    }

    /**
     * Return the most blocked port since first date
     * @return array
     */
    public function getMostBlockedPort() : array
    {
        return $this->model->getMostBlockedPort();
    }

    /**
     * Return the top 10 destination port that have been blocked
     * @return array
     */
    public function getTopTenDestinationPorts(string $date = null, string $ip = null) : array
    {
        return $this->model->getTopTenDestinationPorts($date, $ip);
    }
}
