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
         *  Rendering
         */
        $mylayout = new Layout\Layout();

        /**
         *  Render page
         */
        $mylayout->render();
    }
}
