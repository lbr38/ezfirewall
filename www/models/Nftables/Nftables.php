<?php

namespace Models\Nftables;

use Exception;

class Nftables extends \Models\Model
{
    public function __construct()
    {
        $this->getConnection();
    }

    /**
     * Return the first date of the logs in the database
     * @return string
     */
    public function getFirstDate() : string
    {
        $date = '';

        try {
            // Trick by using a WHERE clause, to make sure to use the index instead of scanning the whole table
            $stmt = $this->db->prepare('SELECT Date FROM nftables_drop WHERE Date > "" ORDER BY Date ASC LIMIT 1');
            $result = $stmt->execute();
        } catch (Exception $e) {
            $this->error($e->getMessage());
        }

        if ($row = $result->fetchArray(SQLITE3_ASSOC)) {
            $date = $row['Date'];
        }

        return $date;
    }

    /**
     * Return the last date of the logs in the database
     * @return string
     */
    public function getLastDate() : string
    {
        $date = '';

        try {
            // Trick by using a WHERE clause, to make sure to use the index instead of scanning the whole table
            $stmt = $this->db->prepare('SELECT Date FROM nftables_drop WHERE Date > "" GROUP BY DATE ORDER BY Id DESC LIMIT 1');
            $result = $stmt->execute();
        } catch (Exception $e) {
            $this->error($e->getMessage());
        }

        if ($row = $result->fetchArray(SQLITE3_ASSOC)) {
            $date = $row['Date'];
        }

        return $date;
    }
}
