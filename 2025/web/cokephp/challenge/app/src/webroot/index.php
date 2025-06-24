<?php
use App\Core\Request;
use App\Core\Router;
use App\Core\Dispatcher;

$appConfig = require_once dirname(__DIR__) . '/config/bootstrap.php';

// Routing
$request = new Request();
$router = new Router($appConfig);
$router->parse($request->getPath());

// Dispatching
$dispatcher = new Dispatcher($router, $appConfig);
$dispatcher->registerPlugin(new \App\Plugins\Analytics());
$dispatcher->dispatch();