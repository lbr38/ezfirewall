<?php

namespace Controllers\Layout\Tab;

class Ip
{
    public static function render()
    {
        \Controllers\Layout\Container\Render::render('ip');
        \Controllers\Layout\Container\Render::render('config');
    }
}
