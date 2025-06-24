<?php
define('BASE_PATH', dirname(__DIR__));
define('APP_PATH', BASE_PATH . '/src');
define('CONFIG_PATH', BASE_PATH . '/config');
define('CONFIG_PREFIX', 'CONFIG_');

require_once APP_PATH . '/functions.php';

spl_autoload_register(function ($className) {
    if (strpos($className, 'App\\') === 0) {
        $classPath = str_replace('\\', DIRECTORY_SEPARATOR, substr($className, 4));
        $filePath = APP_PATH . DIRECTORY_SEPARATOR . strtolower($classPath) . '.php';
        
        if (file_exists($filePath)) {
            require_once $filePath;
            return true;
        }
    }
    return false;
});

$appConfig = require CONFIG_PATH . '/app.php';
return $appConfig;