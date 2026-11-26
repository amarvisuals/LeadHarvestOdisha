"use client";

import React, { useEffect, useState } from "react";
import { motion, useReducedMotion } from "framer-motion";

interface HourglassTimerProps {
  isRunning: boolean;
  isCompleted: boolean;
}

export default function HourglassTimer({ isRunning, isCompleted }: HourglassTimerProps) {
  const shouldReduceMotion = useReducedMotion();
  const [flipCount, setFlipCount] = useState(0);

  useEffect(() => {
    if (!isRunning || isCompleted || shouldReduceMotion) return;

    // Trigger first flip quickly so user sees it right away, then repeat every 3s
    const firstTimeout = setTimeout(() => {
      setFlipCount((prev) => prev + 1);
    }, 1500);

    const interval = setInterval(() => {
      setFlipCount((prev) => prev + 1);
    }, 3000);

    return () => {
      clearTimeout(firstTimeout);
      clearInterval(interval);
    };
  }, [isRunning, isCompleted, shouldReduceMotion]);

  const active = isRunning && !isCompleted;

  return (
    <div className="relative w-36 h-36 flex items-center justify-center">
      {/* Outer rotating dashed ring */}
      <motion.div
        animate={active && !shouldReduceMotion ? { rotate: 360 } : { rotate: 0 }}
        transition={
          active && !shouldReduceMotion
            ? { duration: 8, repeat: Infinity, ease: "linear" }
            : { duration: 0.3 }
        }
        className="absolute inset-0 rounded-full border-2 border-dashed border-brand-400/80"
      />

      {/* Rotating Hourglass Container */}
      <motion.div
        animate={
          active && !shouldReduceMotion
            ? { rotate: flipCount * 180 }
            : { rotate: 0 }
        }
        transition={{ duration: 0.75, ease: [0.65, 0, 0.35, 1] }}
        className="relative w-20 h-28 flex items-center justify-center"
      >
        <svg
          viewBox="0 0 80 110"
          className="w-full h-full drop-shadow-md"
          fill="none"
          xmlns="http://www.w3.org/2000/svg"
        >
          <defs>
            {/* Clip paths matching the exact interior of top & bottom glass bulbs */}
            <clipPath id="topBulbClip">
              <path d="M 14 14 L 66 14 C 61 35 46 47 40 53 C 34 47 19 35 14 14 Z" />
            </clipPath>
            <clipPath id="bottomBulbClip">
              <path d="M 14 96 L 66 96 C 61 75 46 63 40 57 C 34 63 19 75 14 96 Z" />
            </clipPath>
          </defs>

          {/* Glass Contour */}
          <path
            d="M 10 10 L 70 10 C 65 35 48 48 40 55 C 32 48 15 35 10 10 Z"
            fill="rgba(240, 253, 250, 0.9)"
            stroke="#0F766E"
            strokeWidth="3.5"
            strokeLinecap="round"
          />
          <path
            d="M 10 100 L 70 100 C 65 75 48 62 40 55 C 32 62 15 75 10 100 Z"
            fill="rgba(240, 253, 250, 0.9)"
            stroke="#0F766E"
            strokeWidth="3.5"
            strokeLinecap="round"
          />

          {/* Top Sand (Drains smoothly using clipPath + rect y/height) */}
          <g clipPath="url(#topBulbClip)">
            <motion.rect
              x="10"
              width="60"
              fill="#F59E0B"
              initial={{ y: 16, height: 40 }}
              animate={
                active
                  ? { y: [16, 49, 16], height: [40, 6, 40] }
                  : { y: 28, height: 28 }
              }
              transition={
                active
                  ? { duration: 3.0, repeat: Infinity, ease: "easeInOut" }
                  : { duration: 0.3 }
              }
            />
          </g>

          {/* Bottom Sand (Fills smoothly using clipPath + rect y/height) */}
          <g clipPath="url(#bottomBulbClip)">
            <motion.rect
              x="10"
              width="60"
              fill="#D97706"
              initial={{ y: 90, height: 8 }}
              animate={
                active
                  ? { y: [90, 60, 90], height: [8, 38, 8] }
                  : { y: 66, height: 32 }
              }
              transition={
                active
                  ? { duration: 3.0, repeat: Infinity, ease: "easeInOut" }
                  : { duration: 0.3 }
              }
            />
          </g>

          {/* Falling Sand Stream */}
          {active && (
            <motion.line
              x1="40"
              y1="52"
              x2="40"
              y2="94"
              stroke="#F59E0B"
              strokeWidth="2.5"
              strokeDasharray="4 4"
              strokeLinecap="round"
              animate={{ strokeDashoffset: [0, -16] }}
              transition={{ duration: 0.5, repeat: Infinity, ease: "linear" }}
            />
          )}

          {/* Smooth falling sand grains */}
          {active && !shouldReduceMotion && (
            <>
              <motion.circle
                cx="40"
                r="1.8"
                fill="#B45309"
                animate={{ cy: [55, 92], opacity: [1, 0.3] }}
                transition={{ duration: 0.7, repeat: Infinity, ease: "linear" }}
              />
              <motion.circle
                cx="40"
                r="1.5"
                fill="#D97706"
                animate={{ cy: [55, 92], opacity: [1, 0.3] }}
                transition={{ duration: 0.7, repeat: Infinity, ease: "linear", delay: 0.25 }}
              />
              <motion.circle
                cx="40"
                r="1.8"
                fill="#F59E0B"
                animate={{ cy: [55, 92], opacity: [1, 0.3] }}
                transition={{ duration: 0.7, repeat: Infinity, ease: "linear", delay: 0.5 }}
              />
            </>
          )}

          {/* Top & Bottom Stands */}
          <rect x="5" y="4" width="70" height="7" rx="3.5" fill="#0D544E" />
          <rect x="5" y="99" width="70" height="7" rx="3.5" fill="#0D544E" />
        </svg>
      </motion.div>
    </div>
  );
}
