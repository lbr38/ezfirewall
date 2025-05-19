<?php

namespace Controllers\Layout\Tab;

class Home
{
    public static function render()
    {
        \Controllers\Layout\Container\Render::render('charts');
    }
}
