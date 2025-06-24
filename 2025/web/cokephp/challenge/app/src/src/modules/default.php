<?php
namespace App\Modules;

class Index
{
    public function indexAction()
    {
        echo render('index');
    }
}