# HTML Table Extractor (Streamlit)

A small Streamlit web app that lets you upload an HTML file, list the `<table>` elements it contains, preview them, and interactively filter columns (channel / parameter / statistics).

## Run Locally

```powershell
# (optional) create & activate virtual env
python -m venv .venv
.\.venv\Scripts\Activate.ps1

pip install -r requirements.txt
streamlit run extract_table_streamlit.py
```
Then open the URL shown (usually http://localhost:8501).

## Deploy Options

### 1. Streamlit Community Cloud (free, fastest)
1. Create a new public GitHub repo and push these files.
2. Visit https://streamlit.io/cloud -> New app.
3. Choose repo, branch, and set the main file to `extract_table_streamlit.py`.
4. Deploy (build ~1–2 min). Push updates to redeploy automatically.

### 2. Render.com (free tier)
1. Push code to GitHub.
2. In Render dashboard: New + Web Service.
3. Select repo. Runtime: Python. Build command:
	`pip install -r requirements.txt`
	Start command:
	`streamlit run extract_table_streamlit.py --server.port=$PORT --server.address=0.0.0.0`
4. Create service; wait for deploy.

### 3. Heroku
Prereqs: `heroku` CLI installed, account created.
```powershell
heroku login
heroku create html-table-extractor
git init
git add .
git commit -m "Deploy"
heroku git:remote -a html-table-extractor
git push heroku main  # or master depending on branch
```
Uses the added `Procfile`.

### 4. Docker Anywhere
Build and run (local or on a VM / cloud run):
```powershell
# build
docker build -t html-table-extractor .
# run (map host port 8501)
docker run --rm -p 8501:8501 html-table-extractor
```
Then open http://localhost:8501.

### 5. Azure App Service (Container)
1. Build & push Docker image to ACR or Docker Hub.
2. Create Web App for Containers, point to the image, set `WEBSITES_PORT=8501`.

### 6. AWS (Elastic Beanstalk / ECS / Lightsail)
Use the same Docker image; expose port 8501.

### 7. Google Cloud Run (Container, serverless)
```powershell
gcloud builds submit --tag gcr.io/PROJECT_ID/html-table-extractor
gcloud run deploy html-table-extractor --image gcr.io/PROJECT_ID/html-table-extractor --platform managed --allow-unauthenticated --port 8501
```

## Environment Variables
Not required; app is stateless. Max upload size can be raised by adding to `config.toml` if needed.

## Increasing Max Upload Size
Create `.streamlit/config.toml`:
```toml
[server]
maxUploadSize = 200
```
(Value in MB.)

## Project Tree
```
extract_table_streamlit.py
requirements.txt
README.md
```

## License
Provide a license file if you plan to share publicly.
