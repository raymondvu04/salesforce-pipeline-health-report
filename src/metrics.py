import os
import pandas as pd

TODAY = pd.Timestamp.today(tz="UTC").normalize()

def main():
    os.makedirs("data/processed", exist_ok=True)

    opps = pd.read_csv("data/raw/opportunities.csv")
    accts = pd.read_csv("data/raw/accounts.csv")

    # ---- Clean types ----
    for c in ["CreatedDate", "LastModifiedDate", "CloseDate"]:
        if c in opps.columns:
            opps[c] = pd.to_datetime(opps[c], errors="coerce", utc=True)

    opps["Amount"] = pd.to_numeric(opps["Amount"], errors="coerce")

    # days open / modified
    opps["days_open"] = (TODAY - opps["CreatedDate"]).dt.days
    opps["days_since_modified"] = (TODAY - opps["LastModifiedDate"]).dt.days
    
    opps["days_open"] = opps["days_open"].clip(lower=0)
    opps["days_since_modified"] = opps["days_since_modified"].clip(lower=0)


    # ---- Stall logic (simple + explainable) ----
    # Heuristic thresholds by stage (edit later to taste)
    stage_threshold = {
    "Prospecting": 1,
    "Qualification": 2,
    "Needs Analysis": 2,
    "Proposal/Price Quote": 2,
    "Negotiation/Review": 1,
    }


    def stall_threshold(stage):
        return stage_threshold.get(stage, 21)

    opps["stall_threshold_days"] = opps["StageName"].map(stall_threshold)
    opps["is_stalled"] = (opps["IsClosed"] == False) & (opps["days_since_modified"] > opps["stall_threshold_days"])

    # ---- KPIs ----
    total_pipeline = opps.loc[opps["IsClosed"] == False, "Amount"].sum(skipna=True)
    total_open = (opps["IsClosed"] == False).sum()
    total_closed = (opps["IsClosed"] == True).sum()
    won = (opps["IsWon"] == True).sum()
    lost = ((opps["IsClosed"] == True) & (opps["IsWon"] == False)).sum()
    win_rate = won / total_closed if total_closed else 0

    # days to close (won) using close date when available
    opps["days_to_close"] = (opps["CloseDate"] - opps["CreatedDate"]).dt.days
    # Days to close using CloseDate - CreatedDate (won deals only)
    opps["days_to_close"] = (opps["CloseDate"] - opps["CreatedDate"]).dt.days

    valid_won = opps[
    (opps["IsWon"] == True) &
    (opps["days_to_close"].notna()) &
    (opps["days_to_close"] >= 0)
    ]
    avg_days_to_close_won = valid_won["days_to_close"].mean()


    median_days_open_open = opps.loc[opps["IsClosed"] == False, "days_open"].median()

    stalled_count = opps["is_stalled"].sum()
    stalled_value = opps.loc[opps["is_stalled"], "Amount"].sum(skipna=True)

    kpis = pd.DataFrame([{
        "as_of": TODAY.date().isoformat(),
        "open_opportunities": int(total_open),
        "open_pipeline_amount": float(total_pipeline) if pd.notna(total_pipeline) else 0.0,
        "closed_opportunities": int(total_closed),
        "won_opportunities": int(won),
        "lost_opportunities": int(lost),
        "win_rate": float(win_rate),
        "avg_days_to_close_won": float(avg_days_to_close_won) if pd.notna(avg_days_to_close_won) else None,
        "median_days_open_open": float(median_days_open_open) if pd.notna(median_days_open_open) else None,
        "stalled_open_opportunities": int(stalled_count),
        "stalled_pipeline_amount": float(stalled_value) if pd.notna(stalled_value) else 0.0,
    }])

    # pipeline by stage
    stage_tbl = (opps[opps["IsClosed"] == False]
                 .groupby("StageName", dropna=False)
                 .agg(opportunity_count=("Id", "count"),
                      pipeline_amount=("Amount", "sum"),
                      median_days_open=("days_open", "median"),
                      median_days_since_modified=("days_since_modified", "median"))
                 .reset_index()
                 .sort_values(["pipeline_amount"], ascending=False))

    # top stalled opps
    stalled_tbl = (opps[opps["is_stalled"] == True]
                   .merge(accts[["Id","Name"]], how="left", left_on="AccountId", right_on="Id", suffixes=("", "_acct"))
                   .rename(columns={"Name_acct": "AccountName"})
                   [["Id","Name","AccountName","StageName","Amount","days_open","days_since_modified","stall_threshold_days","CloseDate"]]
                   .sort_values(["Amount"], ascending=False)
                   .head(25))

    kpis.to_csv("data/processed/pipeline_kpis.csv", index=False)
    stage_tbl.to_csv("data/processed/pipeline_by_stage.csv", index=False)
    stalled_tbl.to_csv("data/processed/stalled_opportunities.csv", index=False)

    print("Wrote:")
    print(" - data/processed/pipeline_kpis.csv")
    print(" - data/processed/pipeline_by_stage.csv")
    print(" - data/processed/stalled_opportunities.csv")

if __name__ == "__main__":
    main()
