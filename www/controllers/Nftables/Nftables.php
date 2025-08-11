<?php

namespace Controllers\Nftables;

use Exception;

class Nftables
{
    protected $model;

    public function __construct()
    {
        $this->model = new \Models\Nftables\Nftables();
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
}
