"use client";

import React, { useEffect } from "react";
import { motion } from "framer-motion";
import confetti from "canvas-confetti";

interface SuccessConfettiProps {
  leadCount: number;
}

export default function SuccessConfetti({ leadCount }: SuccessConfettiProps) {
  useEffect(() => {
    // Single celebratory burst
    try {
      confetti({
        particleCount: 80,
        spread: 70,
        origin: { y: 0.6 },
        colors: ["#0F766E", "#14B8A6", "#F59E0B", "#10B981"],
      });
    } catch (e) {
      // Fallback gracefully if canvas is unavailable
    }
  }, []);

  return (
    <div className="flex flex-col items-center justify-center text-center p-6">
      {/* Self-drawing checkmark icon */}
      <div className="w-20 h-20 rounded-full bg-emerald-100 flex items-center justify-center text-emerald-600 mb-4 shadow-lg shadow-emerald-500/10 border border-emerald-200">
        <svg className="w-12 h-12" viewBox="0 0 50 50">
          <motion.path
            fill="none"
            stroke="#059669"
            strokeWidth="4.5"
            strokeLinecap="round"
            strokeLinejoin="round"
            d="M 12 26 L 22 36 L 38 15"
            initial={{ strokeDasharray: 50, strokeDashoffset: 50 }}
            animate={{ strokeDashoffset: 0 }}
            transition={{ duration: 0.7, ease: "easeOut" }}
          />
        </svg>
      </div>

      <h2 className="text-2xl sm:text-3xl font-extrabold text-slate-900 mb-2">
        Data Collection Complete!
      </h2>
      <p className="text-slate-600 text-base max-w-md">
        Successfully harvested and deduplicated{" "}
        <span className="font-bold text-emerald-700">{leadCount.toLocaleString()} verified leads</span>.
        Your Excel workbook is formatted and ready for download.
      </p>
    </div>
  );
}
