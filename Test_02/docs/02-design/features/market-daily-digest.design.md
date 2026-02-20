# market-daily-digest Design Document

## 1. Overview
Design guidelines for the Stock Research Market Daily Digest. This dashboard view integrates daily market summaries into a readable React snippet.

## 2. Components
### 2.1 Digest Card
- Renders Title, Date
- Fetches and displays daily highlights

### 2.2 API Connection
- Calls summary endpoint `/api/v1/news/dashboard/summary`
- Parses response for top 3 trends

## 3. Mockup references
- Uses standard tailwind-like utility classes or inline styles.
- Complies with overall project dark mode theme.
