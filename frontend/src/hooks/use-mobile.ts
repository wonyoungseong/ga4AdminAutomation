"use client";

import * as React from "react";

const MOBILE_BREAKPOINT = 768;

export function useIsMobile() {
  const [isMobile, setIsMobile] = React.useState<boolean>(false);

  React.useEffect(() => {
    const mql = window.matchMedia(`(max-width: ${MOBILE_BREAKPOINT - 1}px)`);
    const onChange = () => {
      setIsMobile(window.innerWidth < MOBILE_BREAKPOINT);
    };
    
    // Set initial value
    setIsMobile(window.innerWidth < MOBILE_BREAKPOINT);
    
    mql.addEventListener("change", onChange);
    return () => mql.removeEventListener("change", onChange);
  }, []);

  return isMobile;
}

// Additional mobile-specific hooks
export function useViewportSize() {
  const [size, setSize] = React.useState({ width: 0, height: 0 });

  React.useEffect(() => {
    const updateSize = () => {
      setSize({
        width: window.innerWidth,
        height: window.innerHeight,
      });
    };

    updateSize();
    window.addEventListener('resize', updateSize);
    return () => window.removeEventListener('resize', updateSize);
  }, []);

  return size;
}

export function useDeviceType() {
  const [deviceType, setDeviceType] = React.useState<'mobile' | 'tablet' | 'desktop'>('desktop');

  React.useEffect(() => {
    const updateDeviceType = () => {
      const width = window.innerWidth;
      if (width < 640) {
        setDeviceType('mobile');
      } else if (width < 1024) {
        setDeviceType('tablet');
      } else {
        setDeviceType('desktop');
      }
    };

    updateDeviceType();
    window.addEventListener('resize', updateDeviceType);
    return () => window.removeEventListener('resize', updateDeviceType);
  }, []);

  return deviceType;
}