"use client";

import React from "react";
import { motion, useReducedMotion } from "framer-motion";

interface ProgressLineProps {
  progressPct: number;
}

export default function ProgressLine({ progressPct }: ProgressLineProps) {
  const shouldReduceMotion = useReducedMotion();
  const clamped = Math.min(100, Math.max(0, progressPct));

  return (
    <div className="w-full">
      <div className="flex justify-between items-center text-xs font-semibold text-slate-500 mb-2">
        <span>Overall Progress</span>
        <span className="text-brand-700 font-bold text-sm">{clamped.toFixed(0)}%</span>
      </div>

      <div className="relative w-full h-4 bg-slate-200/80 rounded-full overflow-visible p-0.5 shadow-inner">
        {/* Progress track fill */}
        <motion.div
          className="relative h-full bg-gradient-to-r from-brand-600 via-brand-500 to-teal-400 rounded-full flex items-center justify-end"
          initial={{ width: 0 }}
          animate={{ width: `${clamped}%` }}
          transition={
            shouldReduceMotion
              ? { duration: 0 }
              : { type: "spring", damping: 25, stiffness: 120 }
          }
        >
          {/* Glowing tip highlight */}
          {clamped > 2 && clamped < 100 && (
            <div className="absolute right-0 top-1/2 -translate-y-1/2 w-4 h-4 bg-white rounded-full border-2 border-brand-400 tip-glow z-10" />
          )}
        </motion.div>
      </div>
    </div>
  );
}
