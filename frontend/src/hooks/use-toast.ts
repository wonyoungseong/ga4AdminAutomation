"use client";

import * as React from "react";
import { toast } from "sonner";

type ToastProps = {
  title?: string;
  description?: string;
  variant?: "default" | "destructive";
  action?: React.ReactNode;
  duration?: number;
};

function useToast() {
  return {
    toast: ({ title, description, variant = "default", action, duration }: ToastProps) => {
      if (variant === "destructive") {
        return toast.error(title || description || "오류가 발생했습니다", {
          description: title ? description : undefined,
          duration,
          action,
        });
      }
      
      return toast.success(title || description || "성공적으로 완료되었습니다", {
        description: title ? description : undefined,
        duration,
        action,
      });
    },
    dismiss: toast.dismiss,
  };
}

export { useToast };