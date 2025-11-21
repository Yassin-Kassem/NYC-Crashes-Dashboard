# NYC Motor Vehicle Collisions Dashboard

Interactive data visualization web application for analyzing motor vehicle crashes in New York City (2015-2025).

## 🎯 Project Overview

This dashboard provides comprehensive analysis of NYC motor vehicle collisions through:
- **10 interactive visualizations** answering key research questions
- **Dynamic filtering** by borough, year, vehicle type, and person type
- **Natural language search** functionality
- **Real-time report generation**

## 📊 Research Questions Addressed

1. **Temporal Patterns**: How have injury-related crashes evolved over time in each borough?
2. **Crash Severity**: Which borough has the highest rate of severe crashes?
3. **Victim Analysis**: How do crash patterns differ between pedestrians, cyclists, and occupants?
4. **Contributing Factors**: Which factors are most associated with fatal crashes?
5. **Vehicle Impact**: Are certain vehicle types more likely to be in severe crashes?
6. **Spatial Hotspots**: What are the main geographic hotspots for crashes?
7. **Time-of-Day Risk**: How does crash severity differ between day and night?
8. **Vulnerable Groups**: Which age groups are most vulnerable?
9. **Multi-Vehicle Crashes**: Are multi-vehicle crashes more severe?
10. **Seasonal Trends**: Do we see higher crash severity in winter vs summer?

## 🚀 Features

- ✅ Multiple dropdown filters (Borough, Year, Vehicle Type, Person Type)
- ✅ Search mode with natural language queries
- ✅ "Generate Report" button for dynamic updates
- ✅ 10+ interactive visualizations (bar charts, line charts, maps, heatmaps, pie charts)
- ✅ Real-time data filtering
- ✅ Responsive design

## 🛠️ Tech Stack

- **Backend**: Python, Dash, Plotly
- **Data Processing**: Pandas, NumPy
- **Deployment**: Render/Heroku
- **Data Source**: NYC Open Data (2015-2025)

## 📁 Project Structure

```
nyc-collisions-dashboard/
│
├── app.py                          # Main Dash application
├── requirements.txt                # Python dependencies
├── data/
│   ├── cleaned_collisions_crash_level.csv
│   └── cleaned_collisions_person_level.csv
├── README.md
└── .gitignore
```

## 🔧 Installation & Setup

### Prerequisites
- Python 3.8+
- pip

### Local Installation

1. **Clone the repository**
```bash
git clone https://github.com/yourusername/nyc-collisions-dashboard.git
cd nyc-collisions-dashboard
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Add your data files**
Place the cleaned CSV files in the `data/` folder:
- `cleaned_collisions_crash_level.csv`
- `cleaned_collisions_person_level.csv`

4. **Run the application**
```bash
python app.py
```

5. **Access the dashboard**
Open your browser and go to: `http://localhost:8050`

## 🌐 Deployment (Render)

### Step 1: Prepare for Deployment

1. Create a `Procfile` in your project root:
```
web: gunicorn app:server
```

2. Ensure `requirements.txt` is up to date

### Step 2: Deploy to Render

1. Push your code to GitHub
2. Go to [Render.com](https://render.com) and sign in
3. Click "New +" → "Web Service"
4. Connect your GitHub repository
5. Configure:
   - **Name**: nyc-collisions-dashboard
   - **Environment**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:server`
6. Click "Create Web Service"
7. Wait for deployment (5-10 minutes)

### Step 3: Access Your Deployed App

Your app will be live at: `https://your-app-name.onrender.com`

## 🎨 How to Use

1. **Select Filters**: Choose borough, year, vehicle type, or person type
2. **Search Mode**: Type queries like "Brooklyn 2022 pedestrian crashes"
3. **Generate Report**: Click the blue button to update all visualizations
4. **Interact**: Hover over charts for details, zoom on maps, click legends

## 👥 Team Contributions

**[Member 1 Name]**
- Research Questions: Q1, Q2
- Data Cleaning: Pre-integration crashes dataset
- Website: Temporal and borough visualizations

**[Member 2 Name]**
- Research Questions: Q3, Q4
- Data Cleaning: Pre-integration persons dataset
- Website: Victim analysis and contributing factors charts

**[Member 3 Name]**
- Research Questions: Q5, Q6
- Data Cleaning: Post-integration cleaning
- Website: Vehicle analysis and map visualizations

**[Member 4 Name]**
- Research Questions: Q7, Q8
- Data Cleaning: Data validation
- Website: Time-of-day and age analysis

**[Member 5 Name]** *(if applicable)*
- Research Questions: Q9, Q10
- Data Cleaning: Final documentation
- Website: Multi-vehicle and seasonal analysis

## 📈 Key Insights

*(Add your key findings here after analyzing the data)*

- Finding 1: ...
- Finding 2: ...
- Finding 3: ...

## 📝 Data Sources

- **NYC Motor Vehicle Collisions - Crashes**: [NYC Open Data](https://data.cityofnewyork.us/Public-Safety/Motor-Vehicle-Collisions-Crashes/h9gi-nx95)
- **NYC Motor Vehicle Collisions - Person**: [NYC Open Data](https://data.cityofnewyork.us/Public-Safety/Motor-Vehicle-Collisions-Person/f55k-p6yu)

## 📞 Contact

For questions or feedback, please contact:
- Email: your-email@example.com
- GitHub: [@yourusername](https://github.com/yourusername)

## 📄 License

This project is for educational purposes as part of the Data Engineering and Visualization course at German International University.

---

**Built with ❤️ by [Your Team Name]**