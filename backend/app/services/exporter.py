import csv
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

COLOR_BRAND_TEAL = "0F766E"
COLOR_BRAND_LIGHT = "F0FDFA"
COLOR_ZEBRA = "F8FAFC"
COLOR_BORDER = "CBD5E1"
COLOR_HEADER_TEXT = "FFFFFF"


def style_excel_worksheet(ws, min_col_width: int = 15, max_col_width: int = 45):
    """Auto-fits column widths, applies borders and clean typography."""
    thin_border = Border(
        left=Side(style="thin", color=COLOR_BORDER),
        right=Side(style="thin", color=COLOR_BORDER),
        top=Side(style="thin", color=COLOR_BORDER),
        bottom=Side(style="thin", color=COLOR_BORDER),
    )

    ws.views.sheetView[0].showGridLines = True

    for col in ws.columns:
        max_len = 0
        col_letter = get_column_letter(col[0].column)
        for cell in col:
            if cell.row > 1 and cell.value:
                cell.border = thin_border
            val_str = str(cell.value or "")
            if len(val_str) > max_len:
                max_len = len(val_str)
        fit_width = max(min_col_width, min(max_len + 4, max_col_width))
        ws.column_dimensions[col_letter].width = fit_width


def generate_leads_excel(
    leads: List[Dict[str, Any]],
    skipped_duplicates: List[Dict[str, Any]],
    summary_meta: Dict[str, Any],
    output_path: Path,
) -> Path:
    """
    Generates production-grade, formatted Excel workbook with 3 sheets:
    1. 'Leads' (clean verified leads + Smart Filter & Opportunity columns + clickable links)
    2. 'Summary' (search metrics, states, filters applied, and timing)
    3. 'Skipped Duplicates' (transparency on duplicate rules and sources)
    """
    wb = openpyxl.Workbook()

    # Sheet 1: Leads
    ws_leads = wb.active
    ws_leads.title = "Leads"
    ws_leads.freeze_panes = "A2"

    headers = [
        "Business Name", "Category", "Phone", "Alternate Phone", "Mobile Available",
        "Has Website", "Website", "WhatsApp Link", "Email", "Opportunity Score",
        "Lead Tag", "Address", "Area / Locality", "City", "State", "Pincode",
        "Rating", "Reviews", "Listing URL", "Source", "Collected At"
    ]
    ws_leads.append(headers)

    header_fill = PatternFill(start_color=COLOR_BRAND_TEAL, end_color=COLOR_BRAND_TEAL, fill_type="solid")
    header_font = Font(name="Segoe UI", size=11, bold=True, color=COLOR_HEADER_TEXT)
    header_alignment = Alignment(horizontal="center", vertical="center", wrap_text=False)

    for col_idx in range(1, len(headers) + 1):
        cell = ws_leads.cell(row=1, column=col_idx)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = header_alignment
        cell.border = Border(
            bottom=Side(style="medium", color="0D544E"),
            left=Side(style="thin", color="14B8A6"),
            right=Side(style="thin", color="14B8A6"),
        )
    ws_leads.row_dimensions[1].height = 28

    zebra_fill = PatternFill(start_color=COLOR_ZEBRA, end_color=COLOR_ZEBRA, fill_type="solid")
    link_font = Font(name="Segoe UI", size=10, color="0284C7", underline="single")
    regular_font = Font(name="Segoe UI", size=10)

    for row_idx, lead in enumerate(leads, start=2):
        has_site = "Yes" if lead.get("has_website") or (lead.get("website") and str(lead.get("website")).startswith("http")) else "No"
        mobile_avail = "Yes" if lead.get("mobile_available") or lead.get("phone_clean") else "No"
        wa_link = lead.get("whatsapp_link") or (f"https://wa.me/91{lead['phone_clean']}" if lead.get("phone_clean") else "")

        row_values = [
            lead.get("business_name", ""),
            lead.get("category", ""),
            lead.get("phone", ""),
            lead.get("alt_phone", ""),
            mobile_avail,
            has_site,
            lead.get("website", ""),
            wa_link,
            lead.get("email", ""),
            lead.get("opportunity_score", 0),
            lead.get("lead_tag", "Standard Lead"),
            lead.get("address", ""),
            lead.get("area", ""),
            lead.get("city", ""),
            lead.get("state", "Odisha"),
            lead.get("pincode", ""),
            lead.get("rating", ""),
            lead.get("review_count", ""),
            lead.get("listing_url", ""),
            lead.get("source", "Justdial"),
            str(lead.get("collected_at", ""))[:19],
        ]
        ws_leads.append(row_values)
        ws_leads.row_dimensions[row_idx].height = 20

        is_even = (row_idx % 2 == 0)
        for col_idx in range(1, len(headers) + 1):
            cell = ws_leads.cell(row=row_idx, column=col_idx)
            cell.font = regular_font
            cell.alignment = Alignment(vertical="center")
            if is_even:
                cell.fill = zebra_fill

            val = str(cell.value or "")
            # Clickable links: Website (7), WhatsApp Link (8), Listing URL (19)
            if col_idx in (7, 8, 19) and val.startswith("http"):
                cell.hyperlink = val
                cell.font = link_font

    ws_leads.auto_filter.ref = f"A1:{get_column_letter(len(headers))}{max(len(leads) + 1, 1)}"
    style_excel_worksheet(ws_leads)

    # Sheet 2: Summary
    ws_summary = wb.create_sheet(title="Summary")
    ws_summary.views.sheetView[0].showGridLines = True

    ws_summary.merge_cells("A1:D1")
    title_cell = ws_summary["A1"]
    title_cell.value = "LeadHarvest India – Data Collection Summary"
    title_cell.font = Font(name="Segoe UI", size=14, bold=True, color=COLOR_HEADER_TEXT)
    title_cell.fill = header_fill
    title_cell.alignment = Alignment(horizontal="center", vertical="center")
    ws_summary.row_dimensions[1].height = 36

    filters_applied = summary_meta.get("filters_applied") or {}
    active_filters_str = ", ".join(f"{k}={v}" for k, v in filters_applied.items() if v not in (None, False, "")) or "None (All leads)"

    summary_rows = [
        ("Run Date & Time", summary_meta.get("run_timestamp", datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"))),
        ("Execution Duration", summary_meta.get("duration", "N/A")),
        ("States / UTs Included", ", ".join(summary_meta.get("states", ["Odisha"]))),
        ("Cities / Towns Included", ", ".join(summary_meta.get("cities", []))),
        ("Business Categories", ", ".join(summary_meta.get("categories", []))),
        ("Smart Filters Applied", active_filters_str),
        ("Total Listings Discovered", summary_meta.get("total_found", len(leads) + len(skipped_duplicates))),
        ("Filtered Out by Smart Filters", summary_meta.get("filtered_out_count", 0)),
        ("Duplicates Skipped (Files / DB)", len(skipped_duplicates)),
        ("Final Clean New Leads", len(leads)),
        ("Data Source Adapter", summary_meta.get("adapter", "LeadHarvest Engine")),
        ("Deduplication Engine", "RapidFuzz 3-Tier (Phone -> Name+City -> Fuzzy Name+Addr)"),
    ]

    sec_header_fill = PatternFill(start_color=COLOR_BRAND_LIGHT, end_color=COLOR_BRAND_LIGHT, fill_type="solid")
    sec_font = Font(name="Segoe UI", size=10, bold=True, color="0F766E")

    for i, (k, v) in enumerate(summary_rows, start=3):
        cell_k = ws_summary.cell(row=i, column=1, value=k)
        cell_v = ws_summary.cell(row=i, column=2, value=str(v))
        ws_summary.merge_cells(start_row=i, start_column=2, end_row=i, end_column=4)

        cell_k.font = sec_font
        cell_k.fill = sec_header_fill
        cell_k.alignment = Alignment(vertical="center", indent=1)

        cell_v.font = Font(name="Segoe UI", size=10)
        cell_v.alignment = Alignment(vertical="center", wrap_text=True)
        ws_summary.row_dimensions[i].height = 24

    ws_summary.column_dimensions["A"].width = 30
    ws_summary.column_dimensions["B"].width = 35
    ws_summary.column_dimensions["C"].width = 25
    ws_summary.column_dimensions["D"].width = 25

    # Sheet 3: Skipped Duplicates
    ws_skipped = wb.create_sheet(title="Skipped Duplicates")
    ws_skipped.freeze_panes = "A2"

    skip_headers = ["Business Name", "Phone", "City", "Category", "Duplicate Rule", "Matched Source / File"]
    ws_skipped.append(skip_headers)

    skip_header_fill = PatternFill(start_color="334155", end_color="334155", fill_type="solid")
    for col_idx in range(1, len(skip_headers) + 1):
        cell = ws_skipped.cell(row=1, column=col_idx)
        cell.fill = skip_header_fill
        cell.font = Font(name="Segoe UI", size=11, bold=True, color="FFFFFF")
        cell.alignment = Alignment(horizontal="center", vertical="center")
    ws_skipped.row_dimensions[1].height = 28

    for row_idx, dupe in enumerate(skipped_duplicates, start=2):
        row_vals = [
            dupe.get("business_name", ""),
            dupe.get("phone", ""),
            dupe.get("city", ""),
            dupe.get("category", ""),
            dupe.get("duplicate_rule", "Deduplicated"),
            dupe.get("duplicate_source", "Uploaded File"),
        ]
        ws_skipped.append(row_vals)
        ws_skipped.row_dimensions[row_idx].height = 20
        is_even = (row_idx % 2 == 0)
        for col_idx in range(1, len(skip_headers) + 1):
            cell = ws_skipped.cell(row=row_idx, column=col_idx)
            cell.font = regular_font
            cell.alignment = Alignment(vertical="center")
            if is_even:
                cell.fill = zebra_fill

    ws_skipped.auto_filter.ref = f"A1:{get_column_letter(len(skip_headers))}{max(len(skipped_duplicates) + 1, 1)}"
    style_excel_worksheet(ws_skipped)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    wb.save(output_path)
    return output_path


def generate_leads_csv(leads: List[Dict[str, Any]], output_path: Path) -> Path:
    """Generates clean CSV export for Pro & Agency plans."""
    headers = [
        "Business Name", "Category", "Phone", "Alternate Phone", "Mobile Available",
        "Has Website", "Website", "WhatsApp Link", "Email", "Opportunity Score",
        "Lead Tag", "Address", "Area", "City", "State", "Pincode", "Rating", "Reviews", "Listing URL"
    ]
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        for lead in leads:
            has_site = "Yes" if lead.get("has_website") else "No"
            mobile_avail = "Yes" if lead.get("mobile_available") else "No"
            writer.writerow([
                lead.get("business_name", ""),
                lead.get("category", ""),
                lead.get("phone", ""),
                lead.get("alt_phone", ""),
                mobile_avail,
                has_site,
                lead.get("website", ""),
                lead.get("whatsapp_link", ""),
                lead.get("email", ""),
                lead.get("opportunity_score", 0),
                lead.get("lead_tag", ""),
                lead.get("address", ""),
                lead.get("area", ""),
                lead.get("city", ""),
                lead.get("state", "Odisha"),
                lead.get("pincode", ""),
                lead.get("rating", ""),
                lead.get("review_count", ""),
                lead.get("listing_url", ""),
            ])
    return output_path
