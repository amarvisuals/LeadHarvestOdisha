import { ImageResponse } from "next/og";
import { NextRequest } from "next/server";

export const runtime = "edge";

export async function GET(req: NextRequest) {
  const title = req.nextUrl.searchParams.get("title") || "LeadHarvest India – B2B Lead Data Platform";

  return new ImageResponse(
    (
      <div
        style={{
          width: "1200px",
          height: "630px",
          display: "flex",
          flexDirection: "column",
          justifyContent: "space-between",
          padding: "64px",
          background: "linear-gradient(135deg, #042f2e 0%, #0f766e 55%, #115e59 100%)",
          color: "#ffffff",
          fontFamily: "sans-serif",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: "16px" }}>
          <div
            style={{
              background: "#f59e0b",
              color: "#042f2e",
              padding: "8px 18px",
              borderRadius: "999px",
              fontSize: "20px",
              fontWeight: 800,
            }}
          >
            LEADHARVEST INDIA
          </div>
          <span style={{ fontSize: "20px", color: "#99f6e4" }}>B2B Lead Data Platform</span>
        </div>

        <div style={{ fontSize: "52px", fontWeight: 900, lineHeight: 1.15, maxWidth: "1000px" }}>
          {title}
        </div>

        <div style={{ display: "flex", justifyContent: "space-between", fontSize: "22px", color: "#ccfbf1" }}>
          <span>All 36 States &amp; UTs · No-Website Filter · Smart Dedupe · Excel Export</span>
          <span>4 Free Tries</span>
        </div>
      </div>
    ),
    { width: 1200, height: 630 }
  );
}
