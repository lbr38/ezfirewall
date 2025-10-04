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

        if (!defined('CONFIG')) {
            define('CONFIG', '/opt/ezfirewall/config.yml');
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

        /**
         *  URI
         */
        if (!defined('__ACTUAL_URI__')) {
            /**
             *  If sourceUri is set (POST request from ajax) then we use it
             */
            if (!empty($_POST['sourceUri'])) {
                define('__ACTUAL_URI__', explode('/', $_POST['sourceUri']));
            } else {
                if (!empty($_SERVER["REQUEST_URI"])) {
                    define('__ACTUAL_URI__', explode('/', parse_url($_SERVER["REQUEST_URI"], PHP_URL_PATH)));
                } else {
                    define('__ACTUAL_URI__', '');
                }
            }
        }

        /**
         *  If HTTP_X_REQUESTED_WITH is set to 'xmlhttprequest' we can assume that the request is an AJAX request
         */
        if (!defined('AJAX')) {
            if (!empty($_SERVER['HTTP_X_REQUESTED_WITH']) and strtolower($_SERVER['HTTP_X_REQUESTED_WITH']) === 'xmlhttprequest') {
                define('AJAX', true);
            } else {
                define('AJAX', false);
            }
        }

        /**
         *  Clear cookies starting with 'tables/' or 'temp/' when the page has been reloaded by the user (not AJAX)
         */
        if (AJAX === false) {
            foreach ($_COOKIE as $key => $value) {
                if (strpos($key, 'tables/') === 0 or strpos($key, 'temp/') === 0) {
                    setcookie($key, '', time() - 3600, '/');
                    unset($_COOKIE[$key]);
                }
            }
        }

        if (!empty($_POST['sourceGetParameters']) and is_array($_POST['sourceGetParameters'])) {
            // Merge source GET parameters into the current GET parameters
            $_GET = array_merge($_GET, $_POST['sourceGetParameters']);
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
