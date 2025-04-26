<?php

namespace Models;

use SQLite3;
use Exception;

class Connection extends SQLite3
{
    public function __construct()
    {
        try {
            /**
             *  Open database
             */
            $this->open(DB);
            $this->busyTimeout(30000);
            $this->enableExceptions(true);
            $this->enableWAL();
        } catch (Exception $e) {
            die('Error while trying to open database: ' . $e->getMessage());
        }
    }

    /**
     *  Activate SQLite WAL mode
     */
    private function enableWAL()
    {
        $this->exec('pragma journal_mode = WAL;');
        $this->exec('pragma synchronous = normal;');
        $this->exec('pragma temp_store = memory;');
        $this->exec('pragma mmap_size = 30000000000;');
    }

    /**
     *  Retourne true si le résultat est vide et false si il est non-vide.
     */
    public function isempty($result)
    {
        /**
         *  Compte le nombre de lignes retournées par la requête
         */
        $count = 0;

        while ($row = $result->fetchArray(SQLITE3_ASSOC)) {
            $count++;
        }

        if ($count == 0) {
            return true;
        }

        return false;
    }
}
