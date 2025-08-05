"use client";

import { Sun, Moon, Monitor } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { useTheme } from "@/contexts/theme-context";
import { cn } from "@/lib/utils";

export function ThemeToggle() {
  const { theme, setTheme } = useTheme();

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button 
          variant="ghost" 
          size="icon" 
          className="h-9 w-9 px-0 hover:scale-105 transition-transform duration-200"
          aria-label="테마 변경"
        >
          <Sun className="h-[1.2rem] w-[1.2rem] rotate-0 scale-100 transition-all duration-300 dark:-rotate-90 dark:scale-0" />
          <Moon className="absolute h-[1.2rem] w-[1.2rem] rotate-90 scale-0 transition-all duration-300 dark:rotate-0 dark:scale-100" />
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="w-36">
        <DropdownMenuItem 
          onClick={() => setTheme("light")}
          className={cn(
            "cursor-pointer transition-colors",
            theme === "light" ? "bg-accent text-accent-foreground" : ""
          )}
        >
          <Sun className="mr-2 h-4 w-4" />
          <span className="korean-text">밝은 테마</span>
          {theme === "light" && <span className="ml-auto text-xs">✓</span>}
        </DropdownMenuItem>
        <DropdownMenuItem 
          onClick={() => setTheme("dark")}
          className={cn(
            "cursor-pointer transition-colors",
            theme === "dark" ? "bg-accent text-accent-foreground" : ""
          )}
        >
          <Moon className="mr-2 h-4 w-4" />
          <span className="korean-text">어두운 테마</span>
          {theme === "dark" && <span className="ml-auto text-xs">✓</span>}
        </DropdownMenuItem>
        <DropdownMenuItem 
          onClick={() => setTheme("system")}
          className={cn(
            "cursor-pointer transition-colors",
            theme === "system" ? "bg-accent text-accent-foreground" : ""
          )}
        >
          <Monitor className="mr-2 h-4 w-4" />
          <span className="korean-text">시스템 설정</span>
          {theme === "system" && <span className="ml-auto text-xs">✓</span>}
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}