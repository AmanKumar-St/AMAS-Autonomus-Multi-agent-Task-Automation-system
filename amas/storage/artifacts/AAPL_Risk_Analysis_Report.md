## Task : Calculate Financial Risk Metrics & Sharpe Ratio  
**Asset**: Apple Inc. (AAPL) – USD – NMS exchange  

### 1. Input Data (from Task 1)  
| Item | Value |
|------|-------|
| Number of closing prices (sample size) | **23** |
| Trading days covered | **22** |
| First closing price (oldest) | **$316.22** |
| Last closing price (most recent) | **$338.50** |
| Historical closing series | 316.22, 315.34, 326.57, 332.27, 333.08, 331.34, 332.41, 337.00, 336.13, 338.98, 339.75, 337.02, 335.92, 341.07, 338.40, 329.40, 333.02, 330.32, 333.69, 332.89, 333.63, 336.67, 338.50 |

### 2. Daily Returns (computed from the price series)  

| Day | Return % |
|-----|----------|
| 1 | ‑0.28 % |
| 2 |  +3.56 % |
| 3 |  +1.75 % |
| 4 |  +0.24 % |
| 5 | ‑0.52 % |
| 6 |  +0.32 % |
| 7 |  +1.38 % |
| 8 | ‑0.26 % |
| 9 |  +0.85 % |
| 10 |  +0.23 % |
| 11 | ‑0.80 % |
| 12 | ‑0.33 % |
| 13 |  +1.53 % |
| 14 | ‑0.78 % |
| 15 | ‑2.66 % |
| 16 |  +1.10 % |
| 17 | ‑0.81 % |
| 18 |  +1.02 % |
| 19 | ‑0.24 % |
| 20 |  +0.22 % |
| 21 |  +0.91 % |
| 22 |  +0.54 % |

*Mean daily return (arithmetic average) = **0.317 %** (0.003171 in decimal form).*

### 3. Volatility  

| Metric | Value |
|--------|-------|
| Daily volatility (standard deviation of daily returns) | **1.23 %** |
| Annualized volatility (√252 × daily σ) | **19.5 %** |

### 4. Risk‑Free Rate (from Task 3)  

- **Risk‑free rate (annual)** = **4 %** (0.04 in decimal).

### 5. Performance & Risk Metrics  

| Metric | Value |
|--------|-------|
| Cumulative return over the sample period | **7.05 %** |
| Annualized return (geometric) | **79.92 %** |
| Sharpe Ratio ( (annualized return – risk‑free) / annualized volatility ) | **3.89** |
| Risk Grade (derived from Sharpe) | **EXCELLENT** |

### 6. Interpretation  

- **Mean daily return** of **0.317 %** translates to a very strong **annualized return of ~80 %**, far exceeding the **4 %** risk‑free benchmark.  
- **Annualized volatility** of **19.5 %** indicates moderate price fluctuation relative to the high return.  
- The **Sharpe ratio of 3.89** is well above the typical “good” threshold of 1.0, justifying the **EXCELLENT** risk grade.  

### 7. Deliverable  

A concise, data‑driven report containing:

1. The full list of daily returns (as shown above).  
2. Mean daily return, daily & annualized volatility.  
3. The risk‑free rate used.  
4. Annualized return, cumulative return, Sharpe ratio, and risk grade.  

All figures are directly sourced from the provided price series and the risk‑free rate obtained in the prior task; no external assumptions were introduced.