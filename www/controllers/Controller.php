<?php

namespace Controllers;

require_once('Autoloader.php');

use Exception;

class Controller
{
    public static function render()
    {
        new Autoloader();

        /**
         *  Getting target URI
         */
        $uri = parse_url($_SERVER['REQUEST_URI'], PHP_URL_PATH);
        $uri = explode('/', $uri);
        $targetUri = $uri[1];

        /**
         *  If target URI is 'index.php' then redirect to /
         */
        if ($targetUri == 'index.php') {
            header('Location: /');
        }

        if ($targetUri == '') {
            $targetUri = 'home';
        }

        /**
         *  Rendering
         */
        $mylayout = new Layout\Layout();

        /**
         *  Render page
         */
        $mylayout->render($targetUri);
    }
}
