<?php
namespace App\Plugins;

use App\Models\Analytics as AnalyticsModel;

class Analytics
{
    public function afterLoadModule($moduleName)
    {
        $analyticsModel = new AnalyticsModel();
        $analyticsModel->incrementCount($moduleName);
    }
}