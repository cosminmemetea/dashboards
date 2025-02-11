import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime

# Sample JSON data provided
data = {
    "chart": [
        { "date": "2025-02-05", "ideal_remaining": 25.0, "actual_remaining": 25 },
        { "date": "2025-02-06", "ideal_remaining": 23.75, "actual_remaining": 25 },
        { "date": "2025-02-07", "ideal_remaining": 22.5, "actual_remaining": 16 },
        { "date": "2025-02-08", "ideal_remaining": 21.25, "actual_remaining": 16 },
        { "date": "2025-02-09", "ideal_remaining": 20.0, "actual_remaining": 16 },
        { "date": "2025-02-10", "ideal_remaining": 18.75, "actual_remaining": 0 },
        { "date": "2025-02-11", "ideal_remaining": 17.5, "actual_remaining": 0 },
        { "date": "2025-02-12", "ideal_remaining": 16.25, "actual_remaining": 0 },
        { "date": "2025-02-13", "ideal_remaining": 15.0, "actual_remaining": 0 },
        { "date": "2025-02-14", "ideal_remaining": 13.75, "actual_remaining": 0 },
        { "date": "2025-02-15", "ideal_remaining": 12.5, "actual_remaining": 0 },
        { "date": "2025-02-16", "ideal_remaining": 11.25, "actual_remaining": 0 },
        { "date": "2025-02-17", "ideal_remaining": 10.0, "actual_remaining": 0 },
        { "date": "2025-02-18", "ideal_remaining": 8.75, "actual_remaining": 0 },
        { "date": "2025-02-19", "ideal_remaining": 7.5, "actual_remaining": 0 },
        { "date": "2025-02-20", "ideal_remaining": 6.25, "actual_remaining": 0 },
        { "date": "2025-02-21", "ideal_remaining": 5.0, "actual_remaining": 0 },
        { "date": "2025-02-22", "ideal_remaining": 3.75, "actual_remaining": 0 },
        { "date": "2025-02-23", "ideal_remaining": 2.5, "actual_remaining": 0 },
        { "date": "2025-02-24", "ideal_remaining": 1.25, "actual_remaining": 0 },
        { "date": "2025-02-25", "ideal_remaining": 0.0, "actual_remaining": 0 }
    ]
}

# Convert the date strings into datetime objects
dates = [datetime.strptime(point["date"], "%Y-%m-%d") for point in data["chart"]]
ideal_remaining = [point["ideal_remaining"] for point in data["chart"]]
actual_remaining = [point["actual_remaining"] for point in data["chart"]]

# Create the plot
plt.figure(figsize=(12, 6))
plt.plot(dates, ideal_remaining, label="Ideal Burndown", marker="o", color="blue")
plt.plot(dates, actual_remaining, label="Actual Burndown", marker="o", color="red")

# Set labels and title
plt.xlabel("Date")
plt.ylabel("Remaining Story Points")
plt.title("Sprint Burndown Chart")
plt.legend()
plt.grid(True)

# Format the x-axis for dates
plt.gcf().autofmt_xdate()  # Auto-format date labels
date_formatter = mdates.DateFormatter("%Y-%m-%d")
plt.gca().xaxis.set_major_formatter(date_formatter)

plt.tight_layout()
plt.show()
