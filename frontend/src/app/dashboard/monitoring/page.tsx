"use client";

import { ServiceAccountHealthMonitor } from "@/components/monitoring/service-account-health-monitor";

export default function MonitoringPage() {
  return (
    <div className="space-y-6">
      <ServiceAccountHealthMonitor />
    </div>
  );
}