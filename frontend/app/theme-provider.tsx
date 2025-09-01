"use client";

import { useEffect, useState } from 'react';
import SunCalc from 'suncalc';

function getApproxLocation(): { latitude: number; longitude: number } {
  if (typeof window === 'undefined' || !('geolocation' in navigator)) {
    // Moscow fallback
    return { latitude: 55.7558, longitude: 37.6173 };
  }
  return { latitude: 55.7558, longitude: 37.6173 };
}

function decideThemeNow(date: Date, lat: number, lon: number): 'light' | 'dark' {
  const times = SunCalc.getTimes(date, lat, lon);
  const now = date.getTime();
  const sunset = times.sunset.getTime();
  const sunrise = times.sunrise.getTime();
  // dark between sunset..next sunrise
  if (now >= sunset || now < sunrise) return 'dark';
  return 'light';
}

export function ThemeProvider({ children }: { children: React.ReactNode }) {
  const [theme, setTheme] = useState<'light' | 'dark'>("light");

  useEffect(() => {
    let cancelled = false;
    const html = document.documentElement;

    const applyTheme = (lat: number, lon: number) => {
      const current = decideThemeNow(new Date(), lat, lon);
      if (!cancelled) {
        setTheme(current);
        html.setAttribute('data-theme', current);
      }
    };

    // Try geolocation for better accuracy, fallback to default coords
    if ('geolocation' in navigator) {
      navigator.geolocation.getCurrentPosition(
        (pos) => applyTheme(pos.coords.latitude, pos.coords.longitude),
        () => {
          const { latitude, longitude } = getApproxLocation();
          applyTheme(latitude, longitude);
        },
        { timeout: 3000, maximumAge: 60 * 60 * 1000 }
      );
    } else {
      const { latitude, longitude } = getApproxLocation();
      applyTheme(latitude, longitude);
    }

    // Re-evaluate every 15 minutes
    const id = window.setInterval(() => {
      const { latitude, longitude } = getApproxLocation();
      applyTheme(latitude, longitude);
    }, 15 * 60 * 1000);

    return () => {
      cancelled = true;
      window.clearInterval(id);
    };
  }, []);

  return <>{children}</>;
}
