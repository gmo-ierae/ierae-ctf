<?php
namespace App\Core;

class Router
{
    private string $module = '';
    private string $controller = '';
    private string $action = '';
    private array $params = [];

    public function __construct(array $config)
    {
        $this->module = $config['default_module'] ?? 'default';
        $this->controller = $config['default_controller'] ?? 'Index';
        $this->action = $config['default_action'] ?? 'index';
    }

    /**
     * Parse the request path into module, controller, action, params.
     */
    public function parse(string $path): void
    {
        $path = trim($path, '/');
        $segments = $path ? array_filter(array_map('urldecode', explode('/', $path))) : [];

        if (!empty($segments[0])) {
            $this->module = strtolower($segments[0]);
        }
        if (!empty($segments[1])) {
            $this->controller = ucfirst(strtolower($segments[1]));
        }
        if (!empty($segments[2])) {
            $this->action = strtolower($segments[2]);
        }
        if (count($segments) > 3) {
            $params = array_slice($segments, 3);
            foreach ($params as $key => $value) {
                if ($key % 2 === 1) {
                    $name = $params[$key - 1];
                    if (!is_development()) {
                        $name = preg_replace('/^' . preg_quote(CONFIG_PREFIX) . '/', '', $name);
                    }
                    $this->params[$name] = $value;
                }
            }
        }
    }

    public function getModuleName(): string
    {
        return $this->module;
    }

    public function getControllerName(): string
    {
        return $this->controller;
    }

    public function getActionName(): string
    {
        return $this->action;
    }

    public function getParams(): array
    {
        return $this->params;
    }
}