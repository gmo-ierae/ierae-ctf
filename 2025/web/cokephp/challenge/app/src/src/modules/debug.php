<?php
namespace App\Modules;

if (is_development()) {
    class Debug
    {
        public function phpinfoAction()
        {
            phpinfo();
        }
    }
}