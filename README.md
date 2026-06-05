<<<<<<< HEAD
# OECDash

**Live demo:** https://datathon26-five.vercel.app/

**A fast decision cockpit for foundation leaders and policymakers using OECD private philanthropy data.**

OECDash turns dense funding records into an interactive map, project explorer, funder history view, network analysis tool, and strategy simulator. The goal is simple: help decision-makers spot where money is flowing, where attention is missing, and where the next grant could have the most leverage.

## Why We Built It

Foundation leaders and policymakers often need to answer high-stakes questions quickly:

- Which countries and sectors are receiving the most private philanthropic funding?
- Which areas look underfunded compared with activity and need signals?
- What has a specific funder historically supported?
- Where are funders overlapping, and where is coverage thin?
- If we had a new budget today, where should we deploy it first?

OECDash makes those questions explorable instead of spreadsheet-shaped.

## What It Does

| View | What it helps you do |
| --- | --- |
| **Follow the Money** | Explore global funding flows by country, donor, sector, region, and year. |
| **Discover Projects** | Search and filter funded projects by title, organization, country, sector, donor, and year. |
| **Funding History** | Inspect an organization's funding pattern over time, including sectors, countries, regions, and project records. |
| **Funding Explorer** | Compare funder-country relationships and identify shared, single-source, and weakly covered corridors. |
| **Strategy Simulator** | Allocate a hypothetical grant budget across country-sector opportunities based on risk appetite, white space, concentration, activity, momentum, and strategic goals. |

## Hackathon Highlights

- **Built for action:** the app moves from macro funding patterns to project-level evidence.
- **Decision-ready framing:** rankings are presented as signals, not automatic conclusions.
- **AI-assisted strategy notes:** the simulator can generate concise reasoning for a recommended portfolio.
- **Fast demo path:** map → country profile → funder history → strategy simulator.
- **Responsible by design:** underfunding and similarity signals support review; they do not replace human judgment.

## Demo Flow

1. Start with **Follow the Money** to see the global funding landscape.
2. Click a country to inspect its sector mix, top donors, and local funding profile.
3. Jump into **Funding History** to understand how a funder has behaved over time.
4. Use **Funding Explorer** to compare overlap and weak coverage across selected funders.
5. Finish in **Strategy Simulator** by entering a budget, risk preference, and goal such as:

```text
Support underserved children through health and education programs.
```

## Tech Stack

- **Frontend:** React + Vite
- **Visualization:** Recharts, react-simple-maps, d3-force, d3-scale
- **AI explanation layer:** Anthropic API via `/api/claude`
- **Deployment-ready:** Vercel serverless API route included

## Project Structure

```text
.
+-- api/claude.js                  # Vercel serverless endpoint for AI explanations
+-- data/
|   +-- OECD Dataset.xlsx - complete_p4d3_df.csv  # Source OECD export
+-- flow-map/
|   +-- public/
|   |   +-- flow-data.json         # Aggregated OECD funding data
|   |   +-- projects.json          # Project-level funding records
|   +-- src/
|   |   +-- components/            # Sidebar, map, country profile
|   |   +-- pages/                 # Map, projects, history, network, simulator
|   +-- vite.config.js             # Vite config with local /api/claude middleware
+-- scripts/
    +-- process_flow_data.py       # Builds flow-data.json and projects.json
```

## Run Locally

```bash
cd flow-map
npm install
npm run dev
```

Then open the local Vite URL shown in your terminal.

### Optional: Enable AI Explanations

Create `flow-map/.env`:

```bash
ANTHROPIC_API_KEY=your_api_key_here
```

The dashboard works without this key, but the simulator's AI-generated explanation panel needs it.

## Build

```bash
cd flow-map
npm run build
```

## Data Notes

The prototype uses processed OECD private philanthropy funding data covering **2020-2023**, plus project-level records for exploration and funder history. Amounts are used as directional decision signals for discovery, comparison, and strategy discussion.

The **Follow the Money** KPI cards use full OECD source summaries, including records that may not render as country-to-country map flows. Map layers, donor arcs, and flow charts use the processed mappable country-level records.

Regenerate the app data after changing the source CSV:

```bash
python3 scripts/process_flow_data.py
```

This writes `flow-map/public/flow-data.json` and `flow-map/public/projects.json`, including yearly source KPI summaries used by the year filter.

## Responsible Use

OECDash is designed to support expert review, not automate funding decisions.

- White space is a signal, not proof of need.
- Donor concentration can reveal risk or opportunity, depending on context.
- Historical funding does not equal project quality.
- AI-generated explanations are summaries of the app's scoring logic and should be reviewed by a human decision-maker.

## One-Liner

**OECDash helps funders and policymakers go from OECD funding data to a first-pass strategy in minutes.**
=======
# my-oecd-dashboard
>>>>>>> a2771820ad45c9d49d05d85fcef054a5e397e6f1
