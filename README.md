# dashboards

**Generic Dashboards** is a versatile repository designed to enhance your project management experience on GitHub. This repository provides tools to generate burndown charts and other visual analytics tailored specifically for GitHub projects.

## Features

- **Burndown Chart API**: Automatically calculates ideal vs. actual remaining story points over a sprint.
- **Automatic Sprint Date Retrieval**: Extracts sprint start and end dates from the project's custom "Sprint" iteration field.
- **Multiple Endpoints**:
  - **JSON Endpoint**: `/api/burndownchart` returns the chart data in JSON format.
  - **Image Endpoint**: `/api/burndownchart_image` returns a PNG image of the burndown chart.
  - **Sprints Endpoint**: `/api/sprints` lists available sprints with their start and end dates.
- **Swagger Documentation**: Interactive API docs available at `/apidocs`.
![burn](https://github.com/user-attachments/assets/90ab33ad-7a9d-4ce2-93f3-1ade69cb7653)

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

- The application will be available at http://127.0.0.1:5000.
- View interactive API documentation at: http://127.0.0.1:5000/apidocs

## License

This project is **open source** and available for non-commercial use only. It is licensed under the [MIT License with Commons Clause](https://commonsclause.com/).  
*You may use, modify, and distribute the code freely for non-commercial purposes. Commercial use is not permitted without prior written permission.*
