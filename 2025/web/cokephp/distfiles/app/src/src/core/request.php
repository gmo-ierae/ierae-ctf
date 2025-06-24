<?php
namespace App\Core;

class Request
{
    private string $path;
    private string $method;

    public function __construct()
    {
        $this->path = $this->resolvePath();
        $this->method = strtoupper($_SERVER['REQUEST_METHOD'] ?? 'GET');
    }

    /**
     * Get the clean request path.
     */
    private function resolvePath(): string
    {
        $documentURI = $_SERVER['DOCUMENT_URI'] ?? '/';
        $documentRoot = str_replace('\\', '/', $_SERVER['DOCUMENT_ROOT'] ?? '');
        $scriptPath = dirname(str_replace('\\', '/', $_SERVER['SCRIPT_FILENAME'] ?? ''));
        $basePath = substr($scriptPath, strlen($documentRoot));

        if ($basePath && $basePath !== '/' && strpos($documentURI, $basePath) === 0) {
            $path = substr($documentURI, strlen($basePath));
        } else {
            $path = $documentURI;
        }
        
        // Prepend a slash and remove trailing slash
        $path = '/' . trim($path, '/');
        
        return $path;
    }

    public function getPath(): string
    {
        return $this->path;
    }

    public function getMethod(): string
    {
        return $this->method;
    }
}