# dashboards

**Generic Dashboards** is a versatile repository designed to enhance your project management experience on GitHub. This repository provides tools to generate burndown charts and other visual analytics tailored specifically for GitHub projects.

## Features

- **Burndown Chart API**: Automatically calculates ideal vs. actual remaining story points over a sprint.
- **Automatic Sprint Date Retrieval**: Extracts sprint start and end dates from the project's custom "Sprint" iteration field.
- **Multiple Endpoints**:
  - **JSON Endpoint**: `/api/burndownchart` returns the chart data in JSON format.
  - **Image Endpoint**: `/api/burndownchart_image` returns a PNG image of the burndown chart.
  - **HTML Endpoint**: `/generate` returns an HTML table displaying the chart.
  - **Sprints Endpoint**: `/api/sprints` lists available sprints with their start and end dates.
- **Swagger Documentation**: Interactive API docs available at `/apidocs`.

## Prerequisites

- Python 3.6+
- Git

## Setup Instructions

1. **Clone the Repository**


   git clone https://github.com/yourusername/dashboards.git
   cd dashboards

2. **Create a Virtual Environment**

```python3 -m venv env```

3. **Activate the Virtual Environment**

- On macOS/Linux:
 ```source env/bin/activate```

- On Windows (cmd):
 ``` env\Scripts\activate```

- On Windows (PowerShell):
 ``` .\env\Scripts\Activate.ps1 ```

Install Dependencies
 ```pip install -r requirements.txt```

4. **Running the Application**

Start the Flask application by running:

 ```python app.py```

The application will be available at http://127.0.0.1:5000.
View interactive API documentation at: http://127.0.0.1:5000/apidocs