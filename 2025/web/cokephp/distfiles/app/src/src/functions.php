<?php
    /**
     * Check development mode
     */
    function is_development()
    {
        return getenv('APP_ENV') === 'development';
    }

    /**
     * Escape HTML special characters for safe output.
     */
    function h(string $str)
    {
        return htmlspecialchars($str, ENT_QUOTES);
    }

    /**
     * Render a template file
     */
    function render(string $template, array $data = [])
    {
        $path = BASE_PATH . "/templates/". basename($template) . ".phtml";
        if (!file_exists($path)) {
            throw new \RuntimeException("Template file not found: {$template}");
        }

        extract($data);
        ob_start();
        include $path;
        return ob_get_clean();
    }