import pandas as pd
from ydata_profiling import ProfileReport

df = pd.read_csv('output/simulated_cart_abandons.csv')
profile = ProfileReport(df, title="Cart Abandonment Report")
profile.to_file("your_report.html")