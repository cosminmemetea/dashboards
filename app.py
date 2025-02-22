import os
import re
import traceback
from datetime import datetime, timedelta
from io import BytesIO
import matplotlib
import requests
from flask import render_template

from dotenv import load_dotenv
from flask import Flask, jsonify, request, render_template_string, Response
from flasgger import Swagger
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from flask import send_file 
import json
import numpy as np

# Load environment variables
load_dotenv()
app = Flask(__name__)

# Custom Swagger configuration
swagger_config = {
    "headers": [],
    "specs": [
        {
            "endpoint": "apispec_1",
            "route": "/apispec_1.json",
            "rule_filter": lambda rule: True,
            "model_filter": lambda tag: True,
        }
    ],
    "static_url_path": "/flasgger_static",
    "swagger_ui": True,
    "specs_route": "/apidocs/",
    "info": {
        "title": "Dashboards",
        "version": "1.0.0",
        "description": "API for generating burndown charts from GitHub projects",
        "termsOfService": "https://github.com/cosminmemetea/dashboards/releases",
        "license": {
            "name": "Creative Commons Attribution-NonCommercial 4.0 International License",
            "url": "https://github.com/cosminmemetea/dashboards/blob/main/LICENSE.md"
        },
    }
}

# Initialize Swagger with custom configuration
swagger = Swagger(app, config=swagger_config)

# Default configuration from .env
DEFAULT_GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
DEFAULT_GITHUB_REPO = os.getenv("GITHUB_REPO", "cosminmemetea/dashboards")
DEFAULT_MILESTONE_TITLE = os.getenv("MILESTONE_TITLE", "Milestone I")
DEFAULT_PROJECT_TITLE = os.getenv("PROJECT_TITLE", "Dashboard Project")
DEFAULT_SPRINT_NAME = os.getenv("SPRINT_NAME", "Sprint I")

# Global variables
GITHUB_TOKEN = DEFAULT_GITHUB_TOKEN
GITHUB_REPO = DEFAULT_GITHUB_REPO
MILESTONE_TITLE = DEFAULT_MILESTONE_TITLE
PROJECT_TITLE = DEFAULT_PROJECT_TITLE

try:
    repo_owner, repo_name = GITHUB_REPO.split("/")
except Exception:
    repo_owner, repo_name = ("", "")

# Headers for APIs
HEADERS_REST = {"Authorization": f"token {GITHUB_TOKEN}"}
HEADERS_GRAPHQL = {
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "Content-Type": "application/json"
}
GITHUB_API_URL = "https://api.github.com/graphql"

# Core Functions
def get_milestone_number():
    """Retrieve milestone number for given title."""
    url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/milestones?state=all&per_page=100"
    response = requests.get(url, headers=HEADERS_REST)
    if response.status_code != 200:
        raise Exception(f"Failed to fetch milestones: {response.text}")
    milestones = response.json()
    for ms in milestones:
        if ms.get("title") == MILESTONE_TITLE:
            return ms.get("number")
    raise Exception(f"Milestone '{MILESTONE_TITLE}' not found.")

def fetch_project_id():
    """Fetch project ID for given title."""
    query = """
    query {
      repository(owner: "%s", name: "%s") {
        projectsV2(first: 10) {
          nodes {
            id
            title
          }
        }
      }
    }
    """ % (repo_owner, repo_name)
    response = requests.post(GITHUB_API_URL, headers=HEADERS_GRAPHQL, json={"query": query})
    if response.status_code != 200:
        raise Exception(f"Failed to fetch projects: {response.text}")
    data = response.json()
    if "errors" in data:
        raise Exception(f"GraphQL errors: {data['errors']}")
    projects = data["data"]["repository"]["projectsV2"]["nodes"]
    for project in projects:
        if project["title"] == PROJECT_TITLE:
            return project["id"]
    raise Exception(f"Project '{PROJECT_TITLE}' not found.")

def fetch_custom_fields(project_id):
    """Fetch all custom fields in the project."""
    query = """
    query {
      node(id: "%s") {
        ... on ProjectV2 {
          fields(first: 100) {
            nodes {
              ... on ProjectV2Field {
                id
                name
                __typename
              }
              ... on ProjectV2SingleSelectField {
                id
                name
                __typename
                options {
                  name
                }
              }
              ... on ProjectV2IterationField {
                id
                name
                __typename
                configuration {
                  iterations {
                    startDate
                    duration
                    title
                  }
                }
              }
            }
          }
        }
      }
    }
    """ % project_id
    response = requests.post(GITHUB_API_URL, headers=HEADERS_GRAPHQL, json={"query": query})
    if response.status_code != 200:
        raise Exception(f"Failed to fetch custom fields: {response.text}")
    data = response.json()
    if "errors" in data:
        raise Exception(f"GraphQL errors: {data['errors']}")
    if not data or "data" not in data or "node" not in data["data"]:
        raise Exception(f"Invalid response data: {data}")
    fields = data["data"]["node"]["fields"]["nodes"]
    custom_fields = {}
    for field in fields:
        field_type = field["__typename"]
        field_name = field["name"]
        custom_fields[field_name] = {
            "id": field["id"],
            "type": field_type,
            "options": field.get("options", []),
            "configuration": field.get("configuration", {})
        }
    return custom_fields

def fetch_project_issues(project_id, after_cursor=None):
    """Fetch all issues in the project with pagination, including createdAt."""
    query = """
    query {
      node(id: "%s") {
        ... on ProjectV2 {
          items(first: 100%s) {
            nodes {
              content {
                ... on Issue {
                  id
                  number
                  title
                  state
                  closedAt
                  createdAt  # Added to track task creation date
                }
              }
              fieldValues(first: 20) {
                nodes {
                  ... on ProjectV2ItemFieldSingleSelectValue {
                    name
                    field {
                      ... on ProjectV2SingleSelectField {
                        name
                      }
                    }
                  }
                  ... on ProjectV2ItemFieldTextValue {
                    text
                    field {
                      ... on ProjectV2Field {
                        name
                      }
                    }
                  }
                  ... on ProjectV2ItemFieldNumberValue {
                    number
                    field {
                      ... on ProjectV2Field {
                        name
                      }
                    }
                  }
                  ... on ProjectV2ItemFieldIterationValue {
                    title
                    startDate
                    duration
                    field {
                      ... on ProjectV2IterationField {
                        name
                      }
                    }
                  }
                }
              }
            }
            pageInfo {
              hasNextPage
              endCursor
            }
          }
        }
      }
    }
    """ % (project_id, f', after: "{after_cursor}"' if after_cursor else "")
    response = requests.post(GITHUB_API_URL, headers=HEADERS_GRAPHQL, json={"query": query})
    if response.status_code != 200:
        raise Exception(f"Failed to fetch project issues: {response.text}")
    data = response.json()
    if "errors" in data:
        raise Exception(f"GraphQL errors: {data['errors']}")
    if not data or "data" not in data or "node" not in data["data"]:
        raise Exception(f"Invalid response data: {data}")
    return data

def extract_story_points(field_values, custom_fields):
    """Extract Story Points from project field values."""
    story_points_field = custom_fields.get("Story Points", {})
    field_type = story_points_field.get("type", "")
    for field_value in field_values:
        if "field" in field_value and field_value["field"]["name"] == "Story Points":
            if field_type == "ProjectV2Field" and "number" in field_value:
                return int(field_value["number"]) if field_value["number"] else 0
            elif field_type == "ProjectV2SingleSelectField" and "name" in field_value:
                return int(field_value["name"]) if field_value["name"].isdigit() else 0
            elif field_type == "ProjectV2Field" and "text" in field_value:
                match = re.match(r"(\d+)", field_value["text"])
                return int(match.group(1)) if match else 0
    return 0

def get_issues_for_milestone_and_project():
    """Fetch issues that belong to both milestone and project, including createdAt."""
    milestone_number = get_milestone_number()
    project_id = fetch_project_id()
    custom_fields = fetch_custom_fields(project_id)
    all_issues = []
    after_cursor = None
    
    # Fetch all project issues with pagination
    while True:
        data = fetch_project_issues(project_id, after_cursor)
        items = data["data"]["node"]["items"]["nodes"]
        all_issues.extend(items)
        page_info = data["data"]["node"]["items"]["pageInfo"]
        if not page_info["hasNextPage"]:
            break
        after_cursor = page_info["endCursor"]
    
    # Fetch milestone issues via REST API to get numbers
    url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/issues?milestone={milestone_number}&state=all&per_page=100"
    response = requests.get(url, headers=HEADERS_REST)
    if response.status_code != 200:
        raise Exception(f"Failed to fetch milestone issues: {response.text}")
    milestone_issues = response.json()
    milestone_issue_numbers = {issue["number"] for issue in milestone_issues}
    
    # Filter GraphQL issues by milestone and task title, keeping all fields
    tasks = []
    for item in all_issues:
        if "content" not in item or not item["content"]:
            continue
        issue = item["content"]
        if (issue["number"] in milestone_issue_numbers and 
            "[Task]" in issue["title"] and 
            "createdAt" in issue):  # Ensure createdAt exists
            issue["fieldValues"] = item["fieldValues"]["nodes"]
            tasks.append(issue)
    
    return tasks, custom_fields

def fetch_project_sprints(project_id):
    """Fetch all sprints from project's Sprint Iteration field with status."""
    try:
        custom_fields = fetch_custom_fields(project_id)
        sprint_field = custom_fields.get("Sprint")
        if not sprint_field or sprint_field["type"] != "ProjectV2IterationField":
            raise Exception("Sprint field (Iteration type) not found in project")

        current_date = datetime.now().date()
        sprints = []
        for iteration in sprint_field["configuration"]["iterations"]:
            start_date = datetime.strptime(iteration["startDate"], "%Y-%m-%d").date()
            end_date = (start_date + timedelta(days=iteration["duration"] - 1))

            # Determine status
            if end_date < current_date:
                status = "closed"
            elif start_date > current_date:
                status = "planned"
            else:
                status = "current"

            sprint_info = {
                "title": iteration["title"],
                "start_date": iteration["startDate"],
                "end_date": end_date.strftime("%Y-%m-%d"),
                "status": status
            }
            sprints.append(sprint_info)
        return sprints
    except Exception as e:
        raise Exception(f"Failed to fetch sprints: {str(e)}")

def get_sprint_dates(sprint_name, sprints_list=None):
    """Get start and end dates for a specific sprint."""
    try:
        if sprints_list:
            for sprint in sprints_list:
                if sprint["title"] == sprint_name:
                    return sprint["start_date"], sprint["end_date"]
        
        tasks, _ = get_issues_for_milestone_and_project()
        for issue in tasks:
            for fv in issue.get("fieldValues", []):
                if fv.get("field", {}).get("name") == "Sprint" and "title" in fv:
                    if fv["title"] == sprint_name:
                        start_date = fv["startDate"]
                        end_date = (datetime.strptime(fv["startDate"], "%Y-%m-%d") + 
                                  timedelta(days=fv["duration"] - 1)).strftime("%Y-%m-%d")
                        return start_date, end_date
        raise Exception(f"No sprint dates found for sprint '{sprint_name}'")
    except Exception as e:
        raise Exception(f"Failed to get sprint dates: {str(e)}")

def compute_burndown_chart(sprint_name, sprints_list=None):
    """Compute burndown chart data with initial commitment fixed and scope creep applied from creation date."""
    tasks, custom_fields = get_issues_for_milestone_and_project()
    if not tasks:
        raise Exception(f"No tasks found for milestone '{MILESTONE_TITLE}' in project '{PROJECT_TITLE}'")
    
    sprint_start, sprint_end = get_sprint_dates(sprint_name, sprints_list)
    sprint_start_date = datetime.strptime(sprint_start, "%Y-%m-%d").date()
    sprint_end_date = datetime.strptime(sprint_end, "%Y-%m-%d").date()
    total_days = (sprint_end_date - sprint_start_date).days + 1
    
    # Initial commitment: Sum story points of tasks created before or on sprint start
    initial_points = sum(extract_story_points(issue["fieldValues"], custom_fields)
                         for issue in tasks
                         if datetime.strptime(issue["createdAt"], "%Y-%m-%dT%H:%M:%SZ").date() <= sprint_start_date)
    
    chart = []
    current_total_points = initial_points  # Running total starts with initial commitment
    
    for day_index in range(total_days):
        current_date = sprint_start_date + timedelta(days=day_index)
        
        # Ideal remaining decreases linearly from initial commitment
        ideal_remaining = (initial_points - (initial_points * day_index / (total_days - 1))
                          if total_days > 1 else initial_points)
        
        # Add story points for tasks created up to this date (scope creep)
        day_points = sum(extract_story_points(issue["fieldValues"], custom_fields)
                         for issue in tasks
                         if datetime.strptime(issue["createdAt"], "%Y-%m-%dT%H:%M:%SZ").date() <= current_date)
        current_total_points = day_points  # Update total to include new tasks up to this day
        
        # Calculate completed points up to this date
        completed_points = 0
        for issue in tasks:
            if issue.get("state", "").upper() == "CLOSED" and issue.get("closedAt"):
                closed_date = datetime.strptime(issue["closedAt"], "%Y-%m-%dT%H:%M:%SZ").date()
                if closed_date <= current_date:
                    completed_points += extract_story_points(issue["fieldValues"], custom_fields)
        
        actual_remaining = current_total_points - completed_points
        chart.append({
            "date": current_date.strftime("%Y-%m-%d"),
            "ideal_remaining": round(ideal_remaining, 2),
            "actual_remaining": max(actual_remaining, 0)  # Ensure no negative values
        })
    
    return chart

# Routes
@app.route("/")
def home():
    """Home page with form."""
    form_html = """
    <!DOCTYPE html>
    <html>
    <head>
      <title>Dashboard4Git - Burndown Chart Generator</title>
    </head>
    <body>
      <h1>Dashboard4Git</h1>
      <form action="/generate" method="get">
        <label>GitHub Token:
          <input type="text" name="github_token" value="%s">
        </label><br>
        <label>Repository (owner/repo):
          <input type="text" name="github_repo" value="%s">
        </label><br>
        <label>Milestone Title:
          <input type="text" name="milestone_title" value="%s">
        </label><br>
        <label>Project Title:
          <input type="text" name="project_title" value="%s">
        </label><br>
        <label>Sprint (e.g., "Sprint I"):
          <input type="text" name="sprint" value="%s">
        </label><br>
        <input type="submit" value="Generate Burndown Chart">
      </form>
    </body>
    </html>
    """ % (DEFAULT_GITHUB_TOKEN, DEFAULT_GITHUB_REPO, DEFAULT_MILESTONE_TITLE,
           DEFAULT_PROJECT_TITLE, DEFAULT_SPRINT_NAME)
    return render_template_string(form_html)

@app.route("/generate")
def generate():
    """Generate burndown chart HTML table."""
    global GITHUB_TOKEN, GITHUB_REPO, MILESTONE_TITLE, PROJECT_TITLE, repo_owner, repo_name
    GITHUB_TOKEN = request.args.get("github_token", DEFAULT_GITHUB_TOKEN)
    GITHUB_REPO = request.args.get("github_repo", DEFAULT_GITHUB_REPO)
    MILESTONE_TITLE = request.args.get("milestone_title", DEFAULT_MILESTONE_TITLE)
    PROJECT_TITLE = request.args.get("project_title", DEFAULT_PROJECT_TITLE)
    sprint = request.args.get("sprint", DEFAULT_SPRINT_NAME)
    try:
        repo_owner, repo_name = GITHUB_REPO.split("/")
        HEADERS_REST["Authorization"] = f"token {GITHUB_TOKEN}"
        HEADERS_GRAPHQL["Authorization"] = f"Bearer {GITHUB_TOKEN}"
    except Exception:
        return "Error: github_repo must be in the format 'owner/repo'"
    try:
        project_id = fetch_project_id()
        sprints = fetch_project_sprints(project_id)
        chart = compute_burndown_chart(sprint, sprints)
        html = "<html><head><title>Burndown Chart</title></head><body>"
        html += f"<h1>Burndown Chart for Milestone '{MILESTONE_TITLE}' in Project '{PROJECT_TITLE}'</h1>"
        html += "<table border='1' cellspacing='0' cellpadding='5'><tr><th>Date</th><th>Ideal Remaining</th><th>Actual Remaining</th></tr>"
        for point in chart:
            html += f"<tr><td>{point['date']}</td><td>{point['ideal_remaining']}</td><td>{point['actual_remaining']}</td></tr>"
        html += "</table></body></html>"
        return html
    except Exception as e:
        return "Error: " + str(e)

@app.route("/api/sprints", methods=["GET"])
def api_get_sprints():
    """
    Get all sprints for the project with status.
    ---
    parameters:
      - name: github_token
        in: query
        type: string
        description: GitHub personal access token
      - name: github_repo
        in: query
        type: string
        description: Repository in the format owner/repo
      - name: project_title
        in: query
        type: string
        description: Project title
    responses:
      200:
        description: List of sprints with status
        schema:
          type: array
          items:
            type: object
            properties:
              title:
                type: string
              start_date:
                type: string
              end_date:
                type: string
              status:
                type: string
                enum: [planned, current, closed]
      500:
        description: Error message
    """
    global GITHUB_TOKEN, GITHUB_REPO, PROJECT_TITLE, repo_owner, repo_name
    GITHUB_TOKEN = request.args.get("github_token", DEFAULT_GITHUB_TOKEN)
    GITHUB_REPO = request.args.get("github_repo", DEFAULT_GITHUB_REPO)
    PROJECT_TITLE = request.args.get("project_title", DEFAULT_PROJECT_TITLE)
    try:
        repo_owner, repo_name = GITHUB_REPO.split("/")
        HEADERS_REST["Authorization"] = f"token {GITHUB_TOKEN}"
        HEADERS_GRAPHQL["Authorization"] = f"Bearer {GITHUB_TOKEN}"
    except Exception:
        return jsonify({"error": "github_repo must be in the format 'owner/repo'"}), 400
    try:
        project_id = fetch_project_id()
        sprints = fetch_project_sprints(project_id)
        return jsonify(sprints)
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route("/api/burndownchart", methods=["GET"])
def api_burndown_chart():
    """
    Generate burndown chart data.
    ---
    parameters:
      - name: github_token
        in: query
        type: string
        description: GitHub personal access token
      - name: github_repo
        in: query
        type: string
        description: Repository in the format owner/repo
      - name: milestone_title
        in: query
        type: string
        description: Milestone title
      - name: project_title
        in: query
        type: string
        description: Project title
      - name: sprint
        in: query
        type: string
        description: Sprint name
        default: "Sprint I"
    responses:
      200:
        description: Burndown chart data
        schema:
          type: object
          properties:
            chart:
              type: array
              items:
                type: object
                properties:
                  date:
                    type: string
                  ideal_remaining:
                    type: number
                  actual_remaining:
                    type: number
      500:
        description: Error message
    """
    global GITHUB_TOKEN, GITHUB_REPO, MILESTONE_TITLE, PROJECT_TITLE, repo_owner, repo_name
    GITHUB_TOKEN = request.args.get("github_token", DEFAULT_GITHUB_TOKEN)
    GITHUB_REPO = request.args.get("github_repo", DEFAULT_GITHUB_REPO)
    MILESTONE_TITLE = request.args.get("milestone_title", DEFAULT_MILESTONE_TITLE)
    PROJECT_TITLE = request.args.get("project_title", DEFAULT_PROJECT_TITLE)
    sprint = request.args.get("sprint", DEFAULT_SPRINT_NAME)
    try:
        repo_owner, repo_name = GITHUB_REPO.split("/")
        HEADERS_REST["Authorization"] = f"token {GITHUB_TOKEN}"
        HEADERS_GRAPHQL["Authorization"] = f"Bearer {GITHUB_TOKEN}"
    except Exception:
        return jsonify({"error": "github_repo must be in the format 'owner/repo'"}), 400
    try:
        project_id = fetch_project_id()
        sprints = fetch_project_sprints(project_id)
        chart = compute_burndown_chart(sprint, sprints)
        return jsonify({"chart": chart})
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route("/api/burndownchart_image_bars", methods=["GET"])
def burndown_chart_image_bars():
    """
    Generate a bar chart image of the burndown data with dates, sprint markers, and open/closed points.
    Bars show open (red) and closed (blue) story points, with a dashed line for cumulative burned points
    and a solid trendline for open story points. The first day's open points bar is fixed to the initial
    commitment, and scope creep appears afterward.
    """
    global GITHUB_TOKEN, GITHUB_REPO, MILESTONE_TITLE, PROJECT_TITLE, repo_owner, repo_name
    GITHUB_TOKEN = request.args.get("github_token", DEFAULT_GITHUB_TOKEN)
    GITHUB_REPO = request.args.get("github_repo", DEFAULT_GITHUB_REPO)
    MILESTONE_TITLE = request.args.get("milestone_title", DEFAULT_MILESTONE_TITLE)
    PROJECT_TITLE = request.args.get("project_title", DEFAULT_PROJECT_TITLE)
    sprint = request.args.get("sprint", DEFAULT_SPRINT_NAME)
    save_path = request.args.get("save_path")
    
    try:
        repo_owner, repo_name = GITHUB_REPO.split("/")
        HEADERS_REST["Authorization"] = f"token {GITHUB_TOKEN}"
        HEADERS_GRAPHQL["Authorization"] = f"Bearer {GITHUB_TOKEN}"
    except Exception:
        return jsonify({"error": "github_repo must be in the format 'owner/repo'"}), 400
    
    try:
        project_id = fetch_project_id()
        sprints = fetch_project_sprints(project_id)
        chart_data = compute_burndown_chart(sprint, sprints)
        if not chart_data:
            raise Exception("No chart data found")
        
        # Current date (fixed as per your context)
        current_date = datetime(2025, 2, 22).date()
        
        # Get sprint dates
        sprint_start, sprint_end = get_sprint_dates(sprint, sprints)
        start_date = datetime.strptime(sprint_start, "%Y-%m-%d").date()
        end_date = datetime.strptime(sprint_end, "%Y-%m-%d").date()
        
        # Generate dates excluding weekends up to current date
        dates = []
        current = start_date
        while current <= end_date and current <= current_date:
            if current.weekday() < 5:  # Monday-Friday only
                dates.append(current)
            current += timedelta(days=1)
        
        # Initial commitment from day 1 ideal_remaining
        initial_commitment = chart_data[0]["ideal_remaining"]
        labels = [d.strftime("%Y-%m-%d") for d in dates]
        
        # Initialize with day 1 locked to initial commitment
        open_points = [initial_commitment]
        closed_points = [0]
        cumulative_closed = [0]
        scope_creep_detected = False
        
        # Process days, adjusting for scope creep
        for i, date in enumerate(dates[1:], start=1):
            if i < len(chart_data):
                current_actual = chart_data[i]["actual_remaining"]
                previous_open = open_points[i-1]
                
                # Calculate closed points
                if current_actual < previous_open:
                    daily_closed = previous_open - current_actual
                    closed_points.append(daily_closed)
                    cumulative_closed.append(cumulative_closed[i-1] + daily_closed)
                    open_points.append(current_actual)
                else:
                    closed_points.append(0)
                    cumulative_closed.append(cumulative_closed[i-1])
                    open_points.append(current_actual)
                
                # Detect scope creep
                expected_open = initial_commitment - cumulative_closed[i-1]
                if current_actual > expected_open:
                    scope_creep_detected = True
            else:
                open_points.append(open_points[-1])
                closed_points.append(0)
                cumulative_closed.append(cumulative_closed[-1])
        
        # Adjust day 1 if work was completed
        if chart_data[0]["actual_remaining"] < initial_commitment:
            closed_points[0] = initial_commitment - chart_data[0]["actual_remaining"]
            cumulative_closed[0] = closed_points[0]
        
        # Sprint completion
        burned_points = cumulative_closed[-1]
        sprint_completion = (burned_points / initial_commitment * 100) if initial_commitment > 0 else 0
        
        # Create bar chart
        fig, ax = plt.subplots(figsize=(12, 6))
        x = np.arange(len(labels))
        width = 0.35
        
        ax.bar(x - width/2, open_points, width, label="Open Story Points", color="red")
        ax.bar(x + width/2, closed_points, width, label="Closed Story Points", color="blue")
        ax.plot(x, open_points, "r-", label="Open Points Trend", linewidth=1.5)
        ax.plot(x, cumulative_closed, "g--", label="Cumulative Closed", linewidth=2)
        
        ax.axvline(x=0, color="green", linestyle=":", label="Sprint Start")
        if end_date <= current_date:
            ax.axvline(x=len(dates)-1, color="purple", linestyle=":", label="Sprint End")
        ax.axhline(y=0, color="black", linestyle="-", label="Sprint Completion")
        ax.axhline(y=initial_commitment, color="orange", linestyle="--", label="Initial Commitment", alpha=0.7)
        
        title = f"Burndown Chart - {sprint} (Completion: {sprint_completion:.1f}%)"
        if scope_creep_detected:
            title += " [Scope Creep Detected]"
        ax.set_xlabel("Date")
        ax.set_ylabel("Story Points")
        ax.set_title(title)
        ax.set_xticks(x)
        ax.set_xticklabels(labels, rotation=45)
        ax.legend(loc="best")
        ax.grid(True, axis="y", linestyle="--", alpha=0.7)
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, format="png", bbox_inches="tight")
            plt.close()
            return send_file(save_path, mimetype="image/png", as_attachment=True)
        
        img_io = BytesIO()
        plt.savefig(img_io, format="png", bbox_inches="tight")
        plt.close()
        img_io.seek(0)
        return Response(img_io.getvalue(), mimetype="image/png")
    
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route("/api/burndownchart_image", methods=["GET"])
def burndown_chart_image():
    """
    Generate PNG image of burndown chart and optionally save to specified location.
    ---
    parameters:
      - name: github_token
        in: query
        type: string
        description: GitHub personal access token
      - name: github_repo
        in: query
        type: string
        description: Repository in the format owner/repo
      - name: milestone_title
        in: query
        type: string
        description: Milestone title
      - name: project_title
        in: query
        type: string
        description: Project title
      - name: sprint
        in: query
        type: string
        description: Sprint name
        default: "Sprint I"
      - name: save_path
        in: query
        type: string
        description: Optional file path to save the image (if provided, image will be saved here)
        required: false
    produces:
      - image/png
    responses:
      200:
        description: PNG image of burndown chart
        content:
          image/png:
            schema:
              type: string
              format: binary
      500:
        description: Error message
    """
    global GITHUB_TOKEN, GITHUB_REPO, MILESTONE_TITLE, PROJECT_TITLE, repo_owner, repo_name
    GITHUB_TOKEN = request.args.get("github_token", DEFAULT_GITHUB_TOKEN)
    GITHUB_REPO = request.args.get("github_repo", DEFAULT_GITHUB_REPO)
    MILESTONE_TITLE = request.args.get("milestone_title", DEFAULT_MILESTONE_TITLE)
    PROJECT_TITLE = request.args.get("project_title", DEFAULT_PROJECT_TITLE)
    sprint = request.args.get("sprint", DEFAULT_SPRINT_NAME)
    save_path = request.args.get("save_path")

    try:
        repo_owner, repo_name = GITHUB_REPO.split("/")
        HEADERS_REST["Authorization"] = f"token {GITHUB_TOKEN}"
        HEADERS_GRAPHQL["Authorization"] = f"Bearer {GITHUB_TOKEN}"
    except Exception:
        return jsonify({"error": "github_repo must be in the format 'owner/repo'"}), 400

    try:
        project_id = fetch_project_id()
        sprints = fetch_project_sprints(project_id)
        chart = compute_burndown_chart(sprint, sprints)
        dates = [datetime.strptime(point["date"], "%Y-%m-%d") for point in chart]
        ideal = [point["ideal_remaining"] for point in chart]
        actual = [point["actual_remaining"] for point in chart]

        # Create figure with non-interactive backend (Agg)
        fig = plt.figure(figsize=(10, 6))
        plt.plot(dates, ideal, label="Ideal Burndown", marker="o", color="blue")
        plt.plot(dates, actual, label="Actual Burndown", marker="o", color="red")
        plt.xlabel("Date")
        plt.ylabel("Remaining Story Points")
        plt.title("Sprint Burndown Chart")
        plt.legend()
        plt.grid(True)
        fig.autofmt_xdate()
        plt.gca().xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d"))
        plt.tight_layout()

        # If save_path is provided, save the image there
        if save_path:
            plt.savefig(save_path, format="png", bbox_inches="tight")
            plt.close()
            return send_file(save_path, mimetype="image/png", as_attachment=True)

        # Otherwise, return image in memory
        img_io = BytesIO()
        plt.savefig(img_io, format="png", bbox_inches="tight")
        plt.close()
        img_io.seek(0)
        return Response(img_io.getvalue(), mimetype="image/png")

    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route("/api/burndownchart_image_detailed", methods=["GET"])
def burndown_chart_image_detailed():
    """
    Generate a detailed PNG image of the burndown chart with daily data, sprint dates, and completion status based on burned story points.
    The actual burndown line (red) is rendered only up to the current date.
    ---
    parameters:
      - name: github_token
        in: query
        type: string
        description: GitHub personal access token
      - name: github_repo
        in: query
        type: string
        description: Repository in the format owner/repo
      - name: milestone_title
        in: query
        type: string
        description: Milestone title
      - name: project_title
        in: query
        type: string
        description: Project title
      - name: sprint
        in: query
        type: string
        description: Sprint name
        default: "Sprint I"
      - name: save_path
        in: query
        type: string
        description: Optional file path to save the image
        required: false
    produces:
      - image/png
    responses:
      200:
        description: PNG image of the detailed burndown chart
        content:
          image/png:
            schema:
              type: string
              format: binary
      500:
        description: Error message
    """
    global GITHUB_TOKEN, GITHUB_REPO, MILESTONE_TITLE, PROJECT_TITLE, repo_owner, repo_name
    GITHUB_TOKEN = request.args.get("github_token", DEFAULT_GITHUB_TOKEN)
    GITHUB_REPO = request.args.get("github_repo", DEFAULT_GITHUB_REPO)
    MILESTONE_TITLE = request.args.get("milestone_title", DEFAULT_MILESTONE_TITLE)
    PROJECT_TITLE = request.args.get("project_title", DEFAULT_PROJECT_TITLE)
    sprint = request.args.get("sprint", DEFAULT_SPRINT_NAME)
    save_path = request.args.get("save_path")

    try:
        repo_owner, repo_name = GITHUB_REPO.split("/")
        HEADERS_REST["Authorization"] = f"token {GITHUB_TOKEN}"
        HEADERS_GRAPHQL["Authorization"] = f"Bearer {GITHUB_TOKEN}"
    except Exception:
        return jsonify({"error": "github_repo must be in the format 'owner/repo'"}), 400

    try:
        project_id = fetch_project_id()
        sprints = fetch_project_sprints(project_id)
        chart = compute_burndown_chart(sprint, sprints)

        # Get sprint start and end dates
        sprint_start, sprint_end = get_sprint_dates(sprint, sprints)
        sprint_start_date = datetime.strptime(sprint_start, "%Y-%m-%d")
        sprint_end_date = datetime.strptime(sprint_end, "%Y-%m-%d")
        current_date = datetime.now()

        # Prepare data for chart
        dates = [datetime.strptime(point["date"], "%Y-%m-%d") for point in chart]
        ideal = [point["ideal_remaining"] for point in chart]
        actual = [point["actual_remaining"] for point in chart]

        # Calculate total estimated story points (initial ideal remaining)
        total_estimated_points = ideal[0] if ideal else 0

        # Calculate burned story points (total estimated - actual remaining up to current date)
        current_date_limit = min(current_date, sprint_end_date)
        burned_points = 0
        for i, date in enumerate(dates):
            if date <= current_date_limit:
                burned_points = total_estimated_points - actual[i]

        # Calculate sprint completion based on burned points
        sprint_completion = (burned_points / total_estimated_points * 100) if total_estimated_points > 0 else 0

        # Limit actual data to current date
        actual_dates = [d for d in dates if d <= current_date_limit]
        actual_limited = actual[:len(actual_dates)]

        # Create figure
        fig = plt.figure(figsize=(12, 7))
        ax = plt.gca()

        # Plot ideal burndown (full sprint, blue line)
        plt.plot(dates, ideal, label="Ideal Burndown", marker="o", color="blue")

        # Plot actual burndown (up to current date, red line)
        if actual_dates:
            plt.plot(actual_dates, actual_limited, label="Actual Burndown", marker="o", color="red")

        # Formatting
        plt.xlabel("Date")
        plt.ylabel("Remaining Story Points")
        plt.title(f"Sprint Burndown Chart - {sprint}")
        plt.grid(True, linestyle="--", alpha=0.7)

        # Set x-axis to show all dates with proper formatting
        ax.xaxis.set_major_locator(mdates.DayLocator())
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d"))
        plt.xticks(rotation=45)

        # Add sprint info on the left side (adjusted position)
        info_text = (f"Sprint Start: {sprint_start}\n"
                     f"Sprint End: {sprint_end}\n"
                     f"Completion: {sprint_completion:.1f}%")
        plt.text(0.84, 0.95, info_text, transform=ax.transAxes, fontsize=10,
                 verticalalignment='top', bbox=dict(boxstyle="round,pad=0.3", edgecolor="black", facecolor="white"))

        plt.legend(loc="best")
        plt.tight_layout()

        # Save or return image
        if save_path:
            plt.savefig(save_path, format="png", bbox_inches="tight")
            plt.close()
            return send_file(save_path, mimetype="image/png", as_attachment=True)

        img_io = BytesIO()
        plt.savefig(img_io, format="png", bbox_inches="tight")
        plt.close()
        img_io.seek(0)
        return Response(img_io.getvalue(), mimetype="image/png")

    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500   

CONFIG_FILE = "user_config.json"

@app.route("/api/config", methods=["GET"])
def load_config():
    """Load configuration from file or create default config if not found."""
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            config = json.load(f)
    else:
        # Default configuration based on environment variables
        config = {
            "github_token": DEFAULT_GITHUB_TOKEN,
            "github_repo": DEFAULT_GITHUB_REPO,
            "milestone_title": DEFAULT_MILESTONE_TITLE,
            "project_title": DEFAULT_PROJECT_TITLE,
            "sprint": DEFAULT_SPRINT_NAME
        }
        with open(CONFIG_FILE, "w") as f:
            json.dump(config, f)
    return jsonify(config)

@app.route("/api/config", methods=["POST"])
def save_config():
    """Save configuration provided by the user to a file."""
    try:
        config = request.get_json()
        with open(CONFIG_FILE, "w") as f:
            json.dump(config, f)
        return jsonify({"message": "Configuration saved successfully."}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/ui")
def ui():
    # Pass default config values (from .env) to the template
    return render_template(
        "index.html",
        github_token=DEFAULT_GITHUB_TOKEN,
        github_repo=DEFAULT_GITHUB_REPO,
        milestone_title=DEFAULT_MILESTONE_TITLE,
        project_title=DEFAULT_PROJECT_TITLE,
        sprint_name=DEFAULT_SPRINT_NAME
    )

if __name__ == "__main__":
    app.run(debug=True)