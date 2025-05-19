<?php

namespace Controllers;

use Exception;

class Nftables
{
    public function __construct()
    {
        $this->model = new \Models\Nftables();
    }

    /**
     * Return the first date of the logs in the database
     * @return string
     */
    public function getFirstDate() : string
    {
        return $this->model->getFirstDate();
    }

    /**
     * Return the last date of the logs in the database
     * @return string
     */
    public function getLastDate() : string
    {
        return $this->model->getLastDate();
    }

    /**
     * Return the most blocked IP since first date
     * @return array
     */
    public function getMostBlockedIP() : array
    {
        return $this->model->getMostBlockedIP();
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
    public function getTopTenDestinationPorts(string $date = null) : array
    {
        return $this->model->getTopTenDestinationPorts($date);
    }

    /**
     * Return the top 10 IP address that have been blocked
     * @return array
     */
    public function getTopTenBlockedIPs(string $date = null) : array
    {
        return $this->model->getTopTenBlockedIPs($date);
    }
}
