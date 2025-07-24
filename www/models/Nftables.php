<?php

namespace Models;

use Exception;

class Nftables extends Model
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
            $stmt = $this->db->prepare('SELECT Date FROM nftables_drop ORDER BY Date ASC LIMIT 1');
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
            $stmt = $this->db->prepare('SELECT Date FROM nftables_drop ORDER BY Date DESC LIMIT 1');
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
     * Return all blocked IP
     * It is possible to add an offset to the request
     * @return array
     */
    public function getBlockedIP(bool $withOffset, int $offset) : array
    {
        $data = [];

        try {
            $query = 'SELECT Source_ip, COUNT(*) as Count FROM nftables_drop GROUP BY Source_ip ORDER BY Count DESC';

            // If offset is requested, add it to the query
            if ($withOffset) {
                $query .= ' LIMIT 10 OFFSET :offset';
            }
            $stmt = $this->db->prepare($query);
            $stmt->bindValue(':offset', $offset);
            $result = $stmt->execute();
        } catch (Exception $e) {
            $this->error($e->getMessage());
        }

        while ($row = $result->fetchArray(SQLITE3_ASSOC)) {
            $data[] = $row;
        }

        return $data;
    }

    /**
     * Return the most blocked IP since first date
     * @return array
     */
    public function getMostBlockedIP() : array
    {
        $ip = [];

        try {
            $stmt = $this->db->prepare('SELECT Source_ip, COUNT(*) as Count FROM nftables_drop GROUP BY Source_ip ORDER BY Count DESC LIMIT 1');
            $result = $stmt->execute();
        } catch (Exception $e) {
            $this->error($e->getMessage());
        }

        if ($row = $result->fetchArray(SQLITE3_ASSOC)) {
            $ip = [
                'Source_ip' => $row['Source_ip'],
                'count' => $row['Count']
            ];
        }

        return $ip;
    }

    /**
     * Return blocked port by ip
     * It is possible to add an offset to the request
     * @return array
     */
    public function getBlockedPort(string $ip, bool $withOffset, int $offset) : array
    {
        $ports = [];

        try {
            $query = 'SELECT Dest_port, COUNT(*) as Count FROM nftables_drop WHERE Source_ip = :ip GROUP BY Dest_port ORDER BY Count DESC';

            // If offset is requested, add it to the query
            if ($withOffset) {
                $query .= ' LIMIT 10 OFFSET :offset';
            }

            $stmt = $this->db->prepare($query);
            $stmt->bindValue(':ip', $ip);
            $stmt->bindValue(':offset', $offset);
            $result = $stmt->execute();
        } catch (Exception $e) {
            $this->error($e->getMessage());
        }

        while ($row = $result->fetchArray(SQLITE3_ASSOC)) {
            $ports[] = $row;
        }

        return $ports;
    }

    /**
     * Return the most blocked port since first date
     * @return array
     */
    public function getMostBlockedPort() : array
    {
        $port = [];

        try {
            $stmt = $this->db->prepare('SELECT Dest_port, COUNT(*) as Count FROM nftables_drop GROUP BY Dest_port ORDER BY Count DESC LIMIT 1');
            $result = $stmt->execute();
        } catch (Exception $e) {
            $this->error($e->getMessage());
        }

        if ($row = $result->fetchArray(SQLITE3_ASSOC)) {
            $port = [
                'port' => $row['Dest_port'],
                'count' => $row['Count']
            ];
        }

        return $port;
    }

    /**
     * Return the top 10 destination port that have been blocked at the specified date and time
     * @return array
     */
    public function getTopTenDestinationPorts(string|null $date, string|null $ip) : array
    {
        $data = [];

        try {
            $query = 'SELECT Dest_port, COUNT(*) as Count from nftables_drop';

            // If a date is specified, add it to the query
            if (!empty($date)) {
                $query .= ' WHERE Date = :date';
            }

            // If an IP is specified, add it to the query
            if (!empty($ip)) {
                $query .= ' WHERE Source_ip = :ip';
            }

            $query .= ' GROUP BY Dest_port ORDER BY Count DESC LIMIT 10';

            $stmt = $this->db->prepare($query);
            $stmt->bindValue(':date', $date);
            $stmt->bindValue(':ip', $ip);
            $result = $stmt->execute();
        } catch (Exception $e) {
            $this->error($e->getMessage());
        }

        while ($row = $result->fetchArray(SQLITE3_ASSOC)) {
            $data[] = $row;
        }

        return $data;
    }

    /**
     * Return the top 10 IP address that have been blocked
     * @return array
     */
    public function getTopTenBlockedIPs(string|null $date) : array
    {
        $data = [];

        try {
            $query = 'SELECT Source_ip, COUNT(*) as Count from nftables_drop';

            // If a date is specified, add it to the query
            if (!empty($date)) {
                $query .= ' WHERE Date = :date';
            }
            $query .= ' GROUP BY Source_ip ORDER BY Count DESC LIMIT 10';

            $stmt = $this->db->prepare($query);
            $stmt->bindValue(':date', $date);
            $result = $stmt->execute();
        } catch (Exception $e) {
            $this->error($e->getMessage());
        }

        while ($row = $result->fetchArray(SQLITE3_ASSOC)) {
            $data[] = $row;
        }

        return $data;
    }
}
