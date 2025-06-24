<?php
namespace App\Models;

class Analytics
{
    const PREFIX = 'analytics_';

    /**
     * Increment the count for a specific module.
     */
    public function incrementCount($moduleName)
    {
        $key = $this->getKey($moduleName);
        $count = apcu_fetch($key);
        if ($count === false) {
            $count = 0;
        }
        
        return apcu_store($key, ++$count);
    }
    
    /**
     * Get the count data for all modules.
     */
    public function getCountData()
    {
        $cache = apcu_cache_info();
        $resultData = [];
        
        if (isset($cache['cache_list'])) {
            foreach ($cache['cache_list'] as $entry) {
                $key = $entry['info'];
                if (strpos($key, self::PREFIX) === 0) {
                    $moduleName = substr($key, strlen(self::PREFIX));
                    $resultData[$moduleName] = apcu_fetch($key);
                }
            }
        }
        
        return $resultData;
    }
    
    /**
     * Get the key for apcu storage.
     */
    private function getKey($moduleName)
    {
        return self::PREFIX . $moduleName;
    }
}