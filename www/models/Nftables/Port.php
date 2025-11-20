<?php

namespace Models\Nftables;

use Exception;

class Port extends \Models\Model
{
    public function __construct()
    {
        $this->getConnection();
    }

    /**
     * Return blocked port by ip
     * It is possible to add an offset to the request
     * @return array
     */
    public function getBlockedPortByIp(string $ip, bool $withOffset, int $offset) : array
    {
        $ports = [];

        try {
            $query = 'SELECT Dest_port, Protocol, COUNT(*) as Count FROM nftables_drop WHERE Source_ip = :ip GROUP BY Dest_port,Protocol ORDER BY Count DESC';

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
            $stmt = $this->db->prepare('SELECT Dest_port, Protocol, COUNT(Dest_port) as Count FROM nftables_drop GROUP BY Dest_port, Protocol ORDER BY Count DESC LIMIT 1');
            $result = $stmt->execute();
        } catch (Exception $e) {
            $this->error($e->getMessage());
        }

        if ($row = $result->fetchArray(SQLITE3_ASSOC)) {
            $port = [
                'port' => $row['Dest_port'],
                'protocol' => $row['Protocol'],
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
            $query = 'SELECT Dest_port, Protocol, COUNT(*) as Count from nftables_drop';

            // If a date is specified, add it to the query
            if (!empty($date)) {
                $query .= ' WHERE Date = :date';
            }

            // If an IP is specified, add it to the query
            if (!empty($ip)) {
                $query .= ' WHERE Source_ip = :ip';
            }

            $query .= ' GROUP BY Dest_port,Protocol ORDER BY Count DESC LIMIT 10';

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
     * Count the number of dropped packets for a specific date and port
     * @param string $date
     * @param string $port
     * @return int
     */
    public function countByDatePort(string $date, string $port) : int
    {
        $count = 0;

        try {
            $stmt = $this->db->prepare('SELECT COUNT(*) as Count FROM nftables_drop WHERE Date = :date AND Dest_port = :port');
            $stmt->bindValue(':date', $date);
            $stmt->bindValue(':port', $port);
            $result = $stmt->execute();
        } catch (Exception $e) {
            $this->error($e->getMessage());
        }

        if ($row = $result->fetchArray(SQLITE3_ASSOC)) {
            $count = (int)$row['Count'];
        }

        return $count;
    }
}
