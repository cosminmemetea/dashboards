import os
import re
import traceback
from datetime import datetime, timedelta
from flask import Flask, jsonify
import requests
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()
app = Flask(__name__)

# Required configuration (set these in your .env file)
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")
GITHUB_REPO = os.environ.get("GITHUB_REPO")  # e.g., "cosminmemetea/dashboards"
MILESTONE_TITLE = os.environ.get("MILESTONE_TITLE", "Milestone I")
PROJECT_TITLE = os.environ.get("PROJECT_TITLE", "Dashboard Project")

# Validate environment variables
if not GITHUB_TOKEN or not GITHUB_REPO:
    raise ValueError("Error: GITHUB_TOKEN or GITHUB_REPO not found in .env file")

# Parse repository owner and name
try:
    repo_owner, repo_name = GITHUB_REPO.split("/")
except ValueError:
    raise ValueError("Error: GITHUB_REPO must be in the format 'owner/repo'")

# Headers for REST API
HEADERS_REST = {"Authorization": f"token {GITHUB_TOKEN}"}
# Headers for GraphQL API
HEADERS_GRAPHQL = {
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "Content-Type": "application/json"
}

# GitHub GraphQL API endpoint
GITHUB_API_URL = "https://api.github.com/graphql"

def get_milestone_number():
    """
    Retrieve the milestone number for the given milestone title.
    """
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
    """
    Fetch the project ID for the given project title.
    """
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
    """
    Fetch all custom fields in the project to determine their types.
    """
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
            "options": field.get("options", [])
        }
    return custom_fields

def fetch_project_issues(project_id, after_cursor=None):
    """
    Fetch all issues in the project with pagination, handling different field types.
    """
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
    """
    Extract Story Points from project field values based on field type.
    Returns 0 if not found or invalid.
    """
    story_points_field = custom_fields.get("Story Points", {})
    field_type = story_points_field.get("type", "")

    for field_value in field_values:
        if "field" in field_value and field_value["field"]["name"] == "Story Points":
            if field_type == "ProjectV2Field" and "number" in field_value:
                return int(field_value["number"]) if field_value["number"] else 0
            elif field_type == "ProjectV2SingleSelectField" and "name" in field_value:
                # Try to parse the selected option (e.g., "2")
                return int(field_value["name"]) if field_value["name"].isdigit() else 0
            elif field_type == "ProjectV2Field" and "text" in field_value:
                # Try to parse text (e.g., "2 points")
                match = re.match(r"(\d+)", field_value["text"])
                return int(match.group(1)) if match else 0
    return 0

def get_issues_for_milestone_and_project():
    """
    Fetch issues that belong to both the milestone and the project.
    """
    # Fetch milestone number
    milestone_number = get_milestone_number()

    # Fetch project ID
    project_id = fetch_project_id()

    # Fetch custom fields
    custom_fields = fetch_custom_fields(project_id)
    print("Custom fields in Dashboard Project:")
    for name, details in custom_fields.items():
        print(f"  {name}: Type={details['type']}, ID={details['id']}, Options={details['options']}")

    # Fetch all issues in the project
    all_issues = []
    after_cursor = None
    while True:
        data = fetch_project_issues(project_id, after_cursor)
        items = data["data"]["node"]["items"]["nodes"]
        all_issues.extend(items)

        page_info = data["data"]["node"]["items"]["pageInfo"]
        if not page_info["hasNextPage"]:
            break
        after_cursor = page_info["endCursor"]

    # Fetch milestone issues (REST API)
    url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/issues?milestone={milestone_number}&state=all&per_page=100"
    response = requests.get(url, headers=HEADERS_REST)
    if response.status_code != 200:
        raise Exception(f"Failed to fetch milestone issues: {response.text}")
    milestone_issues = response.json()

    # Filter issues that are in both the project and milestone
    milestone_issue_numbers = {issue["number"] for issue in milestone_issues}
    tasks = []
    for item in all_issues:
        if "content" not in item or not item["content"]:
            continue  # Skip non-issue items
        issue = item["content"]
        if issue["number"] in milestone_issue_numbers and "[Task]" in issue["title"]:
            issue["fieldValues"] = item["fieldValues"]["nodes"]
            tasks.append(issue)
    return tasks, custom_fields

@app.route("/api/burndownchart")
def burndown_chart():
    try:
        tasks, custom_fields = get_issues_for_milestone_and_project()
        if not tasks:
            return jsonify({"error": f"No tasks found for milestone '{MILESTONE_TITLE}' in project '{PROJECT_TITLE}'"}), 404

        # Sum the total story points from project field values
        total_points = sum(extract_story_points(issue["fieldValues"], custom_fields) for issue in tasks)

        # Fetch sprint dates from project or milestone (hardcoded for now)
        sprint_start = datetime.strptime("2025-02-05", "%Y-%m-%d")
        sprint_end = datetime.strptime("2025-02-25", "%Y-%m-%d")
        total_days = (sprint_end - sprint_start).days + 1

        chart = []
        for day_index in range(total_days):
            current_date = sprint_start + timedelta(days=day_index)
            # Ideal burndown: linear decrease from total_points to 0
            if total_days > 1:
                ideal_remaining = total_points - (total_points * day_index / (total_days - 1))
            else:
                ideal_remaining = total_points

            # Actual remaining: subtract story points of tasks closed on or before the current date
            completed_points = 0
            for issue in tasks:
                if issue.get("state", "").upper() == "CLOSED" and issue.get("closedAt"):
                    closed_date = datetime.strptime(issue["closedAt"], "%Y-%m-%dT%H:%M:%SZ")
                    if closed_date.date() <= current_date.date():
                        completed_points += extract_story_points(issue["fieldValues"], custom_fields)
            actual_remaining = total_points - completed_points

            chart.append({
                "date": current_date.strftime("%Y-%m-%d"),
                "ideal_remaining": round(ideal_remaining, 2),
                "actual_remaining": actual_remaining
            })
        return jsonify({"chart": chart})
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)