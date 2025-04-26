<?php

namespace Models;

use Exception;

abstract class Model
{
    protected $db;

    public function getConnection()
    {
        $this->db = new Connection();
    }

    public function getLastInsertRowID()
    {
        return $this->db->lastInsertRowID();
    }

    public function closeConnection()
    {
        $this->db->close();
    }

    protected function error($message)
    {
        throw new Exception('Error while executing database query: ' . $message);
    }
}
