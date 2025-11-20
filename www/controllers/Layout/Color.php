<?php

namespace Controllers\Layout;

class Color
{
    /**
     *  Get a random color from a valid hex colors list
     */
    public static function randomColor(int $i = 1) : string|array
    {
        $randomColors = [];

        $validColors = [
            'rgb(75, 192, 192)', // teal
            '#5993ec', // blue
            '#e0b05f', // gold
            '#24d794', // green
            '#EFBDEB', // light pink
            '#F85A3E', // orange-red
            '#8EB1C7', // light blue
            '#1AC8ED', // cyan
            '#E9D758', // yellow
            '#A259EC', // purple
            '#FFB677', // peach
            '#6EE7B7', // mint
            '#FF6F91', // pink
            '#FFD166', // light yellow
            '#43AA8B', // teal green
            '#3A86FF', // vivid blue
            '#FFBE0B', // vivid yellow
            '#8338EC', // violet
            '#FF006E', // magenta
        ];

        // If only one color is requested, return a single color
        if ($i == 1) {
            return $validColors[array_rand($validColors, 1)];
        }

        // If multiple colors are requested, return an array of random colors, without duplicates
        if ($i > 1) {
            $randomKeys = array_rand($validColors, $i);

            foreach ($randomKeys as $key) {
                $randomColors[] = $validColors[$key];
            }

            return $randomColors;
        }
    }
}
