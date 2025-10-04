<?php

namespace Controllers\Layout\Tab;

class Port
{
    public static function render()
    {
        \Controllers\Layout\Container\Render::render('port');
        \Controllers\Layout\Container\Render::render('config');
    }
}
