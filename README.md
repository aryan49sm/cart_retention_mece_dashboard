# Cart Abandoner Retention Strategy

A customer segmentation system that analyzes cart abandonment behavior and helps create targeted retention campaigns. This project implements MECE (Mutually Exclusive, Collectively Exhaustive) methodology to ensure every customer is placed in exactly one segment for clear campaign targeting.

## What This Project Does

This tool helps e-commerce teams recover abandoned carts by automatically grouping customers into distinct segments based on their behavior patterns. Instead of sending the same generic email to everyone who abandoned a cart, you can target different groups with specific strategies that match their shopping behavior.

The system takes cart abandonment data and creates customer segments using purchase history, engagement levels, and profitability metrics. Each segment gets scored and ranked so marketing teams know which groups to prioritize for their campaigns.

## Live Demo
[View Live App](https://cart-retention-mece-dashboard.streamlit.app/)

## Key Features

**MECE-Based Segmentation**
- Creates non-overlapping customer segments based on purchase behavior
- Uses decision tree methodology with AOV, engagement, and profitability metrics
- Ensures every customer is classified into exactly one segment

**Multi-Dimensional Scoring**
- Conversion Potential: How likely customers are to purchase
- Profitability Score: Revenue potential per customer
- Strategic Fit: Long-term business value alignment
- Campaign Efficiency: Segment size and targeting feasibility

**Interactive Dashboard**
- Real-time segmentation for any 7-day period
- Visual segment trees showing decision logic
- Comprehensive reports with actionable insights
- Export capabilities for marketing team execution

**Synthetic Data Generation**
- Creates realistic cart abandonment datasets for testing
- Models different customer archetypes (Casual, Regular, VIP, Dormant)
- Includes seasonal patterns and behavioral variability

## How It Works

**Step 1: Data Input**
Upload or generate cart abandonment data with customer behavior metrics

**Step 2: Segmentation Engine**
```
All Cart Abandoners → AOV Analysis → Engagement Analysis → Final Segments
                         ↓                 ↓                     ↓
                    (High/Med/Low)  (High/Low Engagement)   (5 Distinct Segments)
```

**Step 3: Scoring and Ranking**
Each segment gets scored on conversion potential, profitability, and strategic value

**Step 4: Campaign Strategy**
Receive specific recommendations for targeting each segment

## Quick Start Guide

### Prerequisites
- Python 3.12+ installed on your system
- Git for cloning the repository

### Step 1: Clone the Repository
```bash
git clone https://github.com/your-username/cart-abandoner-retention-strategy.git
cd cart_abandoner_retention_strategy
```

### Step 2: Set Up Virtual Environment (Recommended)
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Mac/Linux
python3 -m venv venv
source venv/bin/activate
```

### Step 3: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 4: Navigate to Frontend
```bash
cd frontend
```

### Step 5: Launch the Application
```bash
streamlit run app.py
```

### Step 6: Open in Browser
The application will automatically open in your browser at:
```
http://localhost:8501
```

## Usage Guide

### Generate Sample Data
1. Go to "New Analysis Period" in the sidebar
2. Select a 7-day date range
3. Click "Generate Synthetic Data" to create sample cart abandoners
4. Wait for data generation to complete (about 30 seconds)

### Analyze Segments
1. After data generation, click "Run Segmentation Analysis"
2. View the segment tree visualization showing decision logic
3. Explore detailed segment reports with customer counts and metrics
4. Check scoring results to see segment priorities

### Explore Dashboard
- **Segments Summary**: Overview of all customer segments
- **User Mapping**: Individual customer segment assignments
- **MECE Report**: Detailed segmentation methodology and results
- **Tree Visualization**: Interactive decision tree display

### View Documentation
Click the "README" button in the sidebar for comprehensive technical documentation

## Project Structure

```
├── frontend/                  # Streamlit web application
│   ├── app.py                 # Main application file
│   ├── components/            # UI components
│   └── utils/                 # Helper functions
├── data_generation/           # Synthetic data creation
├── requirements.txt           # Python dependencies
├── segmentation_engine.py     # Core segmentation logic
├── segment_scorer.py          # Segment scoring algorithms
└── README.md                
```

## Dependencies

The project uses these main libraries:
- **Streamlit**: Web application framework
- **Pandas**: Data manipulation and analysis
- **Plotly**: Interactive visualizations
- **NumPy**: Numerical computing
- **PyVis**: Network/tree visualizations

## Business Use Cases

### Growth Marketing
- Prioritize resources on highest-potential segments
- Develop segment-specific messaging and offers
- Optimize conversion rates through targeted approaches

### Email Marketing Teams
- Target high-value cart abandoners with premium offers
- Send discount campaigns to price-sensitive segments
- Create re-engagement flows for dormant customers

### Data Analytics Teams
- Understand customer behavior patterns across segments
- Measure campaign performance by segment
- A/B test different retention strategies

## Example Segments

The system typically creates segments like:
- **VIP Active**: High-value customers needing immediate attention
- **Core Engaged**: Regular customers for standard retention campaigns  
- **Price-Sensitive**: Discount-responsive low AOV customers
- **Dormant Low-Value**: Re-engagement campaign candidates
- **At-Risk Medium**: Intervention-needed medium AOV customers