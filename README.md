# News Reports — Group 4

**Modern Data Architectures II**
*Teresa Alvarez, Vikram Bhatt, Alessandro Cristofolini, Matteo Khoueiri, Dominique Robson, & Pengchong Zhao*

---

## Business Case

The same world event is covered very differently depending on where the news is written — yet most people only access their local perspective. There is no unified tool to instantly compare how different countries prioritize topics like politics, sports, technology, health, and business. Manually monitoring international news across countries and categories is slow, fragmented, and unscalable.

**Research Question:** How does each country see and prioritize the same world events across politics, sports, technology, and beyond?

### Our Approach

A fully automated, end-to-end data pipeline that:

1. **Collects** news from two APIs (NewsData.io, NewsAPI.org) across multiple countries and categories
2. **Stores** cleaned and augmented articles in MongoDB Atlas (Silver layer)
3. **Processes** data using PySpark for formatting and enrichment
4. **Summarizes** grouped articles using OpenRouter LLM (NVIDIA Nemotron 3, StepFun Step 3.5 Flash) into concise, country/category-specific digests
5. **Serves** final data through Neo4j and MongoDB (Gold layer)
6. **Visualizes** results on an interactive choropleth dashboard (Streamlit + Plotly)

For the full business case, see [BUSINESS_CASE.md](BUSINESS_CASE.md).

---

## Getting Started

### Prerequisites

- Python 3.10+
- A virtual environment tool (`venv` or `uv`)

### Installation

**1. Clone the repository**

```bash
git clone <repo-url>
cd RedditNewsBot
```

**2. Create and activate a virtual environment**

```bash
python -m venv .venv

# macOS / Linux
source .venv/bin/activate

# Windows
.venv\Scripts\activate
```

**3. Install dependencies**

```bash
pip install -r requirements.txt
```

> **Key dependencies:** `streamlit`, `polars`, `pymongo`, `neo4j`, `requests`, `python-dotenv`, `plotly`, `pyyaml`, `openai`

### Environment Variables

Copy the example file and fill in your credentials:

```bash
cp .envexample .env
```

Then edit `.env` with your actual values:

```env
MONGODB_USERNAME="atlas MongoDB username"
MONGODB_PASSWORD="atlas MongoDB password"

NEWSDATAIO_API_KEY="newsio api key"
NEWSDATAIO_API_URL="https://newsdata.io/api/1/<ENDPOINT>?"

NEWSAPIORG_API_KEY="newsapi.org api key"
NEWSAPIORG_TOP_HEADLINES_URL="https://newsapi.org/v2/top-headlines?"
NEWSAPIORG_SOURCES_URL="https://newsapi.org/v2/top-headlines/sources?"

NEO_J_URI="your neo4j uri"
NEO_J_USERNAME="your neo4j username"
NEO_J_PASSWORD="your neo4j password"

OPENROUTER_API="your openrouter api key"
```

---

## How to Run

### Step 1 — Fetch news and generate summaries

This script fetches articles from both APIs, stores them in MongoDB, and generates AI summaries per country/category. Results are saved to `summaries.json`.

```bash
python news/news.py
```

### Step 2 — Launch the dashboard

```bash
streamlit run app.py
```

The dashboard will open in your browser at `http://localhost:8501`. Use the interactive choropleth map to explore news summaries by country and category.
