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
    // Принудительно светлая тема
    document.documentElement.setAttribute('data-theme', 'light');
    setTheme('light');
  }, []);

  return <>{children}</>;
}
