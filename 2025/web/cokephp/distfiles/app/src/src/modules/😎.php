<?php
namespace App\Modules;

use App\Models\Analytics as AnalyticsModel;

class Analytics
{
    public function indexAction()
    {
        $analyticsModel = new AnalyticsModel();
        $countData = $analyticsModel->getCountData();
        
        echo render('analytics', ['countData' => $countData]);
    }
}