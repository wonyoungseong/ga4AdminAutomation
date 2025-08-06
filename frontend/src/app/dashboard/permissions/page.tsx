"use client";

import React from 'react';
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { PermissionWorkflowIntegration } from "@/components/permissions/permission-workflow-integration";
import { PermissionManagementPage } from "@/components/permissions/permission-management-page";

export default function PermissionsPage() {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight korean-text">권한 관리</h1>
          <p className="text-muted-foreground korean-text">GA4 접근 권한을 관리합니다</p>
        </div>
      </div>

      <Tabs defaultValue="modern" className="w-full">
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="modern" className="korean-text">권한 관리 시스템</TabsTrigger>
          <TabsTrigger value="workflow" className="korean-text">워크플로우 통합</TabsTrigger>
          <TabsTrigger value="legacy" className="korean-text">레거시 시스템</TabsTrigger>
        </TabsList>
        
        <TabsContent value="modern">
          <PermissionManagementPage />
        </TabsContent>
        
        <TabsContent value="workflow">
          <PermissionWorkflowIntegration />
        </TabsContent>
        
        <TabsContent value="legacy" className="space-y-6">
          <div className="text-center py-12 text-gray-500">
            <div className="text-lg font-medium mb-2 korean-text">레거시 시스템</div>
            <p className="text-sm korean-text">
              이전 권한 관리 시스템입니다. 새로운 시스템 사용을 권장합니다.
            </p>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
}