# Cart Abandoner Retention Strategy

A customer segmentation system that analyzes cart abandonment behavior and helps create targeted retention campaigns. This project implements MECE (Mutually Exclusive, Collectively Exhaustive) methodology to ensure every customer is placed in exactly one segment for clear campaign targeting.

## What This Project Does

This tool helps e-commerce teams recover abandoned carts by automatically grouping customers into distinct segments based on their behavior patterns. Instead of sending the same generic email to everyone who abandoned a cart, you can target different groups with specific strategies that match their shopping behavior.

The system takes cart abandonment data and creates customer segments using purchase history, engagement levels, and profitability metrics. Each segment gets scored and ranked so marketing teams know which groups to prioritize for their campaigns.

## How It Works

**Step 1: Load Existing Data**
The system uses pre-existing cart abandonment CSV file with customer behavior data

**Step 2: Select Analysis Period**
Choose a 7-day date range for segmentation analysis

**Step 3: Run Segmentation Engine**
```
All Cart Abandoners → Multi-Dimensional Analysis → Segment Combinations → Size Validation → Final Segments
                              ↓                         ↓                    ↓             
                      AOV (High/Mid/Low)        3×2×2 = 12 Initial      Merge Undersized
                     Engagement (High/Low)         Combinations            Segments     
                    Profitability (High/Low)
```

**Step 4: Scoring and Ranking**
Each segment gets scored on conversion potential, lift vs control, profitability, strategic fit, and size. Undersized segments (below 500 users) are automatically merged with similar segments to ensure campaign viability.

**Step 5: View Results**
Access comprehensive reports, segment mappings, and decision tree visualizations

## Live Demo
[View Live App](https://cart-retention-mece-dashboard.streamlit.app/)

## Key Features


**Synthetic Data Generation**
- Created realistic cart abandonment datasets for testing
- Models different customer archetypes (Casual, Regular, VIP, Dormant)
- Includes seasonal patterns and behavioral variability

**MECE-Based Segmentation**
- Creates non-overlapping customer segments based on purchase behavior
- Uses decision tree methodology with AOV, engagement, and profitability metrics
- Ensures every customer is classified into exactly one segment

**Multi-Dimensional Scoring**
- Conversion Potential: How likely customers are to purchase (30% weight)
- Lift vs Control: Expected campaign performance improvement (25% weight)
- Profitability Score: Revenue potential per customer (20% weight)
- Strategic Fit: Long-term business value alignment (15% weight)
- Size Score: Segment size for campaign efficiency (10% weight)

**Interactive Dashboard**
- Real-time segmentation for any 7-day period
- Visual segment trees showing decision logic
- Comprehensive reports with actionable insights
- Export capabilities for marketing team execution

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

### Load Previous Analysis
1. Go to "Previous Analysis" in the sidebar
2. Select from existing analysis periods in the dropdown
3. View the results from previously run segmentation analyses

### Run New Analysis Period
1. Go to "New Analysis Period" in the sidebar
2. Select a 7-day date range (Start Date and End Date)
3. System validates if analysis already exists for this date range
4. Click "Run New Segmentation Analysis" to process the data
5. Get segmentation within a second

### Explore Results
- **Segments Summary**: Overview of all customer segments with counts and metrics
- **User Mapping**: Individual customer segment assignments
- **MECE Report**: Detailed segmentation methodology and validation results
- **Tree Visualization**: Interactive decision tree showing segmentation logic

### View Documentation
Click the "View README" button in the sidebar for comprehensive technical documentation

## Project Structure

```
├── .streamlit/                    # Streamlit configuration
│   └── config.toml                # App configuration
|
├── frontend/                      # Streamlit web application
│   ├── app.py                     # Main application file
│   ├── components/                # UI components
│   │   ├── csv_display.py         # Segment data visualization
│   │   ├── mece_display.py        # MECE compliance reports
│   │   ├── readme_display.py      # Technical documentation
│   │   ├── tree_visualization.py  # Decision tree display
│   │   └── simple_csv_viewer.py   # CSV data viewer
│   └── utils/                     # Helper functions
│       └── data_processing.py     # Data validation & processing
|
├── data_generation/               # Synthetic data creation tools
│   ├── generate_simulated_data.py # Data generator
│   ├── param_spec.json            # Generation parameters
│   └── csv_ydata_profiling.py     # Data profiling
|
├── output*/                       # Analysis results by date range
|
├── segmentation_engine.py         # Core segmentation logic
├── segment_scorer.py              # Multi-dimensional scoring
├── segment_optimizer.py           # Size constraint handling
├── output_generator.py            # Results compilation
└── data_validator.py              # Input data validation
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