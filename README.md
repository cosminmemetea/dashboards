
# 📊 dashboards


[![Python Version](https://img.shields.io/badge/python-3.11-blue.svg)](https://www.python.org/)
[![Dockerized](https://img.shields.io/badge/docker-ready-blue)](https://hub.docker.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Flask](https://img.shields.io/badge/Flask-2.3-green)](https://flask.palletsprojects.com/)
[![Swagger Docs](https://img.shields.io/badge/docs-Swagger-yellow)](http://localhost:5051/apidocs)
[![Last Commit](https://img.shields.io/github/last-commit/cosminmemetea/dashboards)](https://github.com/cosminmemetea/dashboards)
[![Issues](https://img.shields.io/github/issues/cosminmemetea/dashboards)](https://github.com/cosminmemetea/dashboards/issues)

---

**Generic Dashboards** is a powerful and configurable analytics engine for GitHub Projects (Projects v2). It generates burndown charts and visual analytics tailored to sprint tracking, iteration planning, and velocity monitoring.

---

## 🚀 Features

- **📉 Burndown Chart Generator**
  - Tracks ideal vs. actual story points.
  - Scope creep detection with dynamic visualization.
- **🧠 Automatic Sprint Detection**
  - Reads `Sprint` iterations from GitHub Projects v2.
- **🎯 API Endpoints**
  - `/api/burndownchart`: JSON chart data
  - `/api/burndownchart_image`: PNG image
  - `/api/burndownchart_image_detailed`: Detailed annotated PNG
  - `/api/burndownchart_image_bars`: Open vs Closed SP bar chart
  - `/api/sprints`: Sprint schedule info
- **📖 Swagger Docs**: Built-in Flasgger UI at `/apidocs`
- **🖥️ Optional Web UI** at `/ui`

---

## 🛠️ Installation

### 1. Clone the Repo

```bash
git clone https://github.com/cosminmemetea/dashboards.git
cd dashboards
```

### 2. Create a Virtual Environment

```bash
python3 -m venv env
source env/bin/activate  # macOS/Linux
# or
env\Scripts\activate  # Windows
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Run the App

```bash
python app.py
```

Visit:
- App UI: [http://127.0.0.1:5000/ui](http://127.0.0.1:5000/ui)
- API Docs: [http://127.0.0.1:5000/apidocs](http://127.0.0.1:5000/apidocs)

---

### 5. Docker support
docker build -t dashboards-app .
docker run -p 80:80 dashboards-app
http://localhost/ui 

## 🧪 cURL API Examples

### ➕ Submit Config

```bash
curl -X POST http://localhost:5000/api/config \
  -H "Content-Type: application/json" \
  -d @user_config.json
```

### 📊 Get Chart Image

```bash
curl http://localhost:5000/api/burndownchart_image > chart.png
```

---

## 📦 PyInstaller Packaging

**macOS**

```bash
pyinstaller --name Dashboards \
            --windowed \
            --add-data "LICENSE.md:." \
            --add-data "README.md:." \
            --hidden-import matplotlib \
            --hidden-import flasgger \
            --onefile app.py
```

**Windows**

```bash
pyinstaller --name Dashboards ^
            --windowed ^
            --add-data "LICENSE.md;." ^
            --add-data "README.md;." ^
            --hidden-import matplotlib ^
            --hidden-import flasgger ^
            --onefile app.py
```

---

## 🧩 GitHub Project Setup

1. **Milestones**: Define them for sprints/releases.
2. **Issues**: Add `[Task]` prefix and a numeric `Story Points` label.
3. **GitHub Projects v2**:
   - Add `Story Points` (number field).
   - Add `Sprint` (iteration field).
4. **Link Issues to the Project**.

See full instructions in the original documentation above for detailed setup.

---

## 📸 Screenshots

![burn](https://github.com/user-attachments/assets/90ab33ad-7a9d-4ce2-93f3-1ade69cb7653)
![image](https://github.com/user-attachments/assets/c8b7c112-2d3d-430a-ab8b-7c9e62b0d825)

---

## 📄 License
MIT – Permissive open-source license allowing free use, modification, and distribution for any purpose, with minimal restrictions.

## 🤝 Contributing
Contributions make this repo better! Whether fixing bugs, adding features, or improving docs, you're welcome. Let's have fun!
