<?php

namespace Controllers;

use Exception;

class Autoloader
{
    public function __construct()
    {
        if (!defined('ROOT')) {
            define('ROOT', '/opt/ezfirewall/www');
        }

        if (!defined('DATA_DIR')) {
            define('DATA_DIR', '/var/lib/ezfirewall');
        }

        if (!defined('DB')) {
            define('DB', DATA_DIR . '/ezfirewall.db');
        }

        if (!defined('VERSION')) {
            if (!file_exists('/opt/ezfirewall/version') or !is_readable('/opt/ezfirewall/version')) {
                define('VERSION', 'Unknown');
            } else {
                define('VERSION', trim(file_get_contents('/opt/ezfirewall/version')));
            }
        }

        $this->register();
    }

    /**
     *  Class autoload
     */
    private function register()
    {
        spl_autoload_register(function ($className) {
            $className = str_replace('\\', '/', $className);
            $className = str_replace('Models', 'models', $className);
            $className = str_replace('Controllers', 'controllers', $className);

            if (file_exists(ROOT . '/' . $className . '.php')) {
                require_once(ROOT . '/' . $className . '.php');
            }
        });
    }
}
