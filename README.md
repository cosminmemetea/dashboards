# dashboards

**Generic Dashboards** is a versatile repository designed to enhance your project management experience on GitHub. This repository provides tools to generate burndown charts and other visual analytics tailored specifically for GitHub projects.

## Features

- **Burndown Chart API**: Automatically calculates ideal vs. actual remaining story points over a sprint, with support for:
  - Fixed initial commitment based on tasks present at sprint start.
  - Scope creep detection and visualization starting from the day new tasks are added.
- **Automatic Sprint Date Retrieval**: Extracts sprint start and end dates from the project's custom "Sprint" iteration field.
- **Multiple Endpoints**:
  - **JSON Endpoint**: `/api/burndownchart` returns the chart data in JSON format.
  - **Image Endpoint**: `/api/burndownchart_image` returns a PNG image of the burndown chart.
  - **Detailed Image Endpoint**: `/api/burndownchart_image_detailed` provides a detailed chart with sprint info and completion percentage.
  - **Bar Chart Endpoint**: `/api/burndownchart_image_bars` generates a bar chart showing open and closed story points, with trendlines and scope creep markers.
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

- The application will be available at http://127.0.0.1:5000/ui
- View interactive API documentation at: http://127.0.0.1:5000/apidocs


## Packing the application

MacOS
pyinstaller --name Dashboards \
            --windowed \
            --add-data "LICENSE.md:." \
            --add-data "README.md:." \
            --hidden-import matplotlib \
            --hidden-import flasgger \
            --onefile app.py

Windwos
pyinstaller --name Dashboards ^
            --windowed ^
            --add-data "LICENSE.md;." ^
            --add-data "README.md;." ^
            --hidden-import matplotlib ^
            --hidden-import flasgger ^
            --onefile app.py
## GitHub Project Configuration

To ensure the dashboards tool works correctly, please set up your GitHub project as follows:

### 1. Milestones
- **Create Milestones** in your GitHub repository for each sprint or release.
- **Assign Issues** to a milestone (e.g., "Milestone I").  
  The script uses the milestone title (from the `.env` file) to filter issues for chart generation.

### 2. GitHub Issues (Tasks)
- **Create Issues** in your repository to represent your work items.
- **Task Identification**:  
  Prefix the title of issues that represent tasks with `"[Task]"`.  
  This is used by the tool to filter out only the tasks when generating the burndown chart.
- **Story Points**:  
  Use a label or a custom field named **"Story Points"** to specify the effort for each task.  
  The tool expects a numerical value (e.g., `Story Points: 3`) to calculate the total work.

### 3. GitHub Project (Projects v2)
- **Create a GitHub Project** (using the new Projects v2 interface) for your repository.
- **Add the Required Custom Fields**:
  - **Story Points**:  
    Create a custom field (of type **Field**) named **"Story Points"**.  
    This field is used to capture the numeric value of each task's effort.
  - **Sprint**:  
    Create a custom field of type **Iteration** named **"Sprint"**.  
    Configure this field with iterations representing your sprints.  
    Each iteration should include:
    - **Title**: The sprint name (e.g., "Sprint I").
    - **Start Date**: The starting date of the sprint (in `YYYY-MM-DD` format).
    - **Duration**: The number of days in the sprint (this field is used to calculate the end date).
  
  The tool will automatically read the iteration information (start date and duration) from the **Sprint** field to determine the sprint timeline.

### 4. Linking Issues to the Project
- **Add Issues to the GitHub Project**:  
  Ensure that your task issues (with "[Task]" in the title) are added to the GitHub Project.  
  This allows the tool to fetch these issues along with their custom field values.

### Summary
For the dashboards tool to work as intended, your repository should have:
- **Milestones** defined for grouping issues by sprint or release.
- **Issues** that are tagged as tasks (with "[Task]" in the title) and assigned to a milestone.
- A **GitHub Project (Projects v2)** configured with custom fields:
  - **"Story Points"** (to capture effort)
  - **"Sprint"** (an Iteration field with properly configured iterations, including start dates and durations)

Following this setup will allow the tool to automatically retrieve sprint dates, compute the burndown chart, and generate visual outputs through the provided API endpoints.

## License

This project is **open source** and available for non-commercial use only. It is licensed under the [Creative Commons Attribution-NonCommercial 4.0 International License](https://creativecommons.org/licenses/by-nc/4.0/).  
*You may use, modify, and distribute the code freely for non-commercial purposes. Commercial use is not permitted without prior written permission.*

