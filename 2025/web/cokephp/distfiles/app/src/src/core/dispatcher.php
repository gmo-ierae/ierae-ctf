<?php
namespace App\Core;

class Dispatcher
{
    private string $moduleName;
    private string $controllerName;
    private string $actionName;
    private array $params;
    private array $config;
    private array $plugins = [];

    public function __construct(Router $router, array $config)
    {
        $this->moduleName = $router->getModuleName();
        $this->controllerName = $router->getControllerName();
        $this->actionName = $router->getActionName();
        $this->params = $router->getParams();
        $this->config = $this->applyDevelopmentConfig($config);
    }

    /**
     * Register the plugin
     */
    public function registerPlugin(object $plugin): self
    {
        if (!method_exists($plugin, 'afterLoadModule')) {
            throw new \InvalidArgumentException('Plugin must have afterLoadModule method');
        }
        $this->plugins[] = $plugin;
        return $this;
    }

    /**
     * Dispatch the request to the appropriate controller action.
     */
    public function dispatch(): void
    {
        $moduleName = $this->moduleName;
        $moduleNamespace = $this->config['module_namespace'] ?? 'App\\Modules';
        $controllerClassName = $this->controllerName;
        $actionMethodName = $this->actionName . 'Action';

        // Load the module file
        try {
            $this->loadModule($moduleName);
        } catch (\Throwable $e) {
            $this->sendErrorResponse(404, "Not Found", "Module '{$moduleName}' not found.");
            return;
        }

        foreach ($this->plugins as $plugin) {
            $plugin->afterLoadModule($moduleName);
        }

        // Create the controller instance
        try {
            $controllerInstance = $this->getControllerInstance($moduleNamespace, $controllerClassName);
        } catch (\Throwable $e) {
            $this->sendErrorResponse(404, "Not Found", "Controller '{$moduleName}::{$controllerClassName}' not found.");
            return;
        }

        // Check if action method exists
        if (!method_exists($controllerInstance, $actionMethodName)) {
            $this->sendErrorResponse(404, "Not Found", "Action '{$actionMethodName}' not found in controller '{$moduleNamespace}\\{$controllerClassName}'.");
            return;
        }

        // Call the action method
        try {
            call_user_func([$controllerInstance, $actionMethodName]);
        } catch (\Throwable $e) {
            $this->sendErrorResponse(500, "Internal Server Error", "An error occurred while executing the action.");
            return;
        }
    }

    /**
     * Apply development config.
     */
    private function applyDevelopmentConfig($config)
    {
        $configParams = array_filter($this->params, function($key) {
            return strpos($key, CONFIG_PREFIX) === 0;
        }, ARRAY_FILTER_USE_KEY);

        if (!empty($configParams)) {
            foreach ($configParams as $key => $value) {
                $varName = substr($key, 7);
                if (isset($config[$varName])) {
                    $config[$varName] = $value;
                }
            }
        }
        return $config;
    }

    /**
     * Load the module file.
     */
    private function loadModule(string $moduleName)
    {
        $modulePath = APP_PATH . "/modules/" . basename($moduleName) . ".php";
        if (!file_exists($modulePath)) {
            throw new \RuntimeException("Module file not found: {$modulePath}");
        }
        require_once $modulePath;
    }

    /**
     * Get the controller instance.
     */
    private function getControllerInstance(string $moduleNamespace, string $controllerClassName)
    {
        $controllerClassName = $moduleNamespace . '\\' . $controllerClassName;
        if (!class_exists($controllerClassName)) {
            throw new \RuntimeException("Controller class not found: {$controllerClassName}");
        }
        return new $controllerClassName();
    }

    /**
     * Send a simple HTTP error response.
     */
    private function sendErrorResponse(int $code, string $status, string $message): void
    {
        if (!headers_sent()) {
           header("HTTP/1.1 {$code} {$status}");
           header("Content-Type: text/html; charset=UTF-8");
        }

        echo "<h1>" . h($code) . " " . h($status) . "</h1>";
        if ($this->config['debug'] ?? false) {
            echo "<p>" . h($message) . "</p>";
        }
        exit;
    }
}