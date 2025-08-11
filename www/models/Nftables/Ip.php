<?php

namespace Models\Nftables;

use Exception;

class Ip extends \Models\Model
{
    public function __construct()
    {
        $this->getConnection();
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
     * Return the list of blocked IPs for a specific port
     * It is possible to add an offset to the request
     * @return array
     */
    public function getBlockedIpByPort(int $port, bool $withOffset, int $offset) : array
    {
        $data = [];

        try {
            $query = 'SELECT Source_ip, Protocol, COUNT(*) as Count FROM nftables_drop WHERE Dest_port = :port GROUP BY Source_ip, Protocol ORDER BY Count DESC';

            if ($withOffset) {
                $query .= ' LIMIT 10 OFFSET :offset';
            }

            $stmt = $this->db->prepare($query);
            $stmt->bindValue(':port', $port);
            $stmt->bindValue(':offset', $offset, SQLITE3_INTEGER);
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
    public function getTopTenBlockedIp(string|null $date) : array
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

    /**
     * Return the top 10 IP address that have been blocked, by port and protocol (optional)
     * @return array
     */
    public function getTopTenBlockedIpByPort(int $port, string|null $protocol) : array
    {
        $data = [];

        try {
            if (!empty($protocol)) {
                $query = 'SELECT Source_ip, COUNT(*) as Count FROM nftables_drop WHERE Dest_port = :port AND Protocol = :protocol GROUP BY Source_ip ORDER BY Count DESC LIMIT 10';
            } else {
                $query = 'SELECT Source_ip, COUNT(*) as Count FROM nftables_drop WHERE Dest_port = :port GROUP BY Source_ip ORDER BY Count DESC LIMIT 10';
            }
            $stmt = $this->db->prepare($query);
            $stmt->bindValue(':port', $port);
            $stmt->bindValue(':protocol', $protocol);
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
     * Return the most blocked IP
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
}
