<?php

namespace Controllers\Layout;

use Exception;
use Datetime;

class Layout
{
    public function render(string $tab = 'home')
    {
        $class = '\Controllers\Layout\Tab' . '\\' . ucfirst($tab);

        if (class_exists($class)) {
            ob_start();

            $class::render();

            $content = ob_get_clean();

            include_once(ROOT . '/views/layout.html.php');
        } else {
            $this->notFound();
        }
    }

    /**
     *  Render Not found page
     */
    private function notFound()
    {
        include_once(ROOT . '/public/custom_errors/custom_404.html');
    }
}
