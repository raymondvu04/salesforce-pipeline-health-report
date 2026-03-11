import os
import pandas as pd
import matplotlib.pyplot as plt

from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch


def money(x):
    try:
        return "${:,.0f}".format(float(x))
    except Exception:
        return str(x)


def pct(x):
    try:
        return "{:.1%}".format(float(x))
    except Exception:
        return str(x)


def make_stage_chart(stage_csv: str, out_png: str):
    df = pd.read_csv(stage_csv)

    # Keep top 8 stages by pipeline amount
    if "pipeline_amount" not in df.columns or "StageName" not in df.columns:
        raise ValueError("pipeline_by_stage.csv must include StageName and pipeline_amount columns")

    df = df.sort_values("pipeline_amount", ascending=False).head(8)

    plt.figure(figsize=(10, 4))
    plt.bar(df["StageName"].astype(str), df["pipeline_amount"])
    plt.xticks(rotation=25, ha="right")
    plt.ylabel("Open Pipeline Amount")
    plt.title("Open Pipeline by Stage (Top 8)")
    plt.tight_layout()
    plt.savefig(out_png, dpi=200)
    plt.close()


def draw_table(c, x, y, col_widths, rows, row_height=14, max_rows=None):
    """Simple table drawer."""
    if max_rows:
        rows = rows[:max_rows]
    for r, row in enumerate(rows):
        yy = y - r * row_height
        for i, cell in enumerate(row):
            c.drawString(x + sum(col_widths[:i]) + 2, yy, str(cell)[:80])


def main():
    os.makedirs("reports", exist_ok=True)

    # ---- Load processed outputs ----
    kpis_df = pd.read_csv("data/processed/pipeline_kpis.csv")
    if kpis_df.empty:
        raise ValueError("pipeline_kpis.csv is empty. Run: python src/metrics.py")
    kpis = kpis_df.iloc[0].to_dict()

    stalled = pd.read_csv("data/processed/stalled_opportunities.csv")
    stage_csv = "data/processed/pipeline_by_stage.csv"

    # ---- Create chart image ----
    chart_path = "reports/pipeline_by_stage.png"
    make_stage_chart(stage_csv, chart_path)

    # ---- Start PDF ----
    pdf_path = "reports/pipeline_health_report.pdf"
    c = canvas.Canvas(pdf_path, pagesize=letter)
    width, height = letter

    # Title
    c.setFont("Helvetica-Bold", 22)
    c.drawString(0.8 * inch, height - 0.9 * inch, "Automated Sales Pipeline Health Report")

    c.setFont("Helvetica", 12)
    c.drawString(0.8 * inch, height - 1.2 * inch, f"As of: {kpis.get('as_of','')}")

    # KPI Summary
    c.setFont("Helvetica-Bold", 18)
    c.drawString(0.8 * inch, height - 1.85 * inch, "KPI Summary")

    c.setFont("Helvetica", 14)

    def safe_float(v):
        try:
            return float(v)
        except Exception:
            return None

    avg_days_to_close = safe_float(kpis.get("avg_days_to_close_won"))
    med_days_open = safe_float(kpis.get("median_days_open_open"))

    kpi_lines = [
        f"Open opportunities: {int(kpis.get('open_opportunities', 0))}",
        f"Open pipeline amount: {money(kpis.get('open_pipeline_amount', 0))}",
        f"Closed opportunities: {int(kpis.get('closed_opportunities', 0))}",
        f"Win rate (closed): {pct(kpis.get('win_rate', 0))}",
        f"Avg days to close (won): {avg_days_to_close:.1f}" if avg_days_to_close is not None else "Avg days to close (won): N/A",
        f"Median days open (open opps): {med_days_open:.1f}" if med_days_open is not None else "Median days open (open opps): N/A",
        f"Stalled open opportunities: {int(kpis.get('stalled_open_opportunities', 0))}",
        f"Stalled pipeline amount: {money(kpis.get('stalled_pipeline_amount', 0))}",
    ]

    yy = height - 2.25 * inch
    for line in kpi_lines:
        c.drawString(1.0 * inch, yy, line)
        yy -= 0.28 * inch

    # Pipeline Distribution header
    c.setFont("Helvetica-Bold", 18)
    c.drawString(0.8 * inch, yy - 0.25 * inch, "Pipeline Distribution")

    # Chart
    c.drawImage(
        chart_path,
        0.8 * inch,
        yy - 2.55 * inch,
        width=6.9 * inch,
        height=2.1 * inch,
        preserveAspectRatio=True,
        mask="auto",
    )

    # Top stalled header
    c.setFont("Helvetica-Bold", 18)
    c.drawString(0.8 * inch, yy - 3.05 * inch, "Top Stalled Opportunities (by Amount)")

    # Build stalled table rows (Top 10) with fallback message
    stalled_top = stalled.head(10).copy()

    if not stalled_top.empty:
        # shorten for layout
        if "Name" in stalled_top.columns:
            stalled_top["Name"] = stalled_top["Name"].astype(str).str.slice(0, 28)
        if "AccountName" in stalled_top.columns:
            stalled_top["AccountName"] = stalled_top["AccountName"].astype(str).str.slice(0, 20)

        rows = [["Opp Name", "Account", "Stage", "Amount", "Days Since Mod"]] + [
            [
                r.get("Name", ""),
                r.get("AccountName", ""),
                r.get("StageName", ""),
                money(r.get("Amount", "")),
                int(r.get("days_since_modified", 0)),
            ]
            for _, r in stalled_top.iterrows()
        ]
    else:
        rows = [
            ["Opp Name", "Account", "Stage", "Amount", "Days Since Mod"],
            ["No stalled opportunities found (based on current thresholds).", "", "", "", ""],
        ]

    # Draw table
    c.setFont("Helvetica", 10)
    x = 0.8 * inch
    y = yy - 3.35 * inch
    col_widths = [2.2 * inch, 1.6 * inch, 1.2 * inch, 1.3 * inch, 1.6 * inch]
    draw_table(c, x, y, col_widths, rows, row_height=14, max_rows=11)

    c.showPage()
    c.save()

    print(f"Saved PDF report to: {pdf_path}")


if __name__ == "__main__":
    main()