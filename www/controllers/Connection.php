<?php

namespace Controllers;

class Connection
{
    private $model;

    public function __construct()
    {
        $this->model = new \Models\Connection();
    }

    public function isempty($result)
    {
        return $this->model->isempty($result);
    }
}
