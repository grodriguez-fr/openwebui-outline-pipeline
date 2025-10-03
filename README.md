# OpenWebUI – Outline Pipeline

A custom pipeline for [OpenWebUI](https://github.com/open-webui/open-webui) that connects with [Outline](https://www.getoutline.com/) (wiki) to let the AI:

- List collections
- Explore documents inside collections
- Retrieve document content
- Answer natural language questions by navigating the wiki

## 🚀 How it works
The pipeline exposes a function `ask_wiki(query)` that:
1. Fetches available collections from Outline
2. Identifies relevant collections and documents
3. Retrieves document content
4. Returns a synthesized response to the user

## 📂 Project structure

```
.
├─ docker-compose.yml # Service definition for OpenWebUI Pipelines
├─ pipelines/
│  └─ ask_wiki.py     # Main pipeline logic
```

## ⚙️ Setup & Deployment

### 1. Clone the repository
```bash
git clone https://github.com/your-org/openwebui-outline-pipeline.git
cd openwebui-outline-pipeline
```

### 2. Configure environment variables
You need to provide:

- `OUTLINE_API_BASE` → API base URL (e.g. `https://wiki.ject.fr/api`)
- `OUTLINE_API_TOKEN` → API token from Outline

Edit them directly in `docker-compose.yml` or export them in your environment.

### 3. Start the pipelines service
```bash
docker compose up -d
```
This will start the OpenWebUI Pipelines service on port `9099`.
All `.py` files in the `pipelines/` folder will be auto-loaded.

### 4. Connect to your OpenWebUI instance
- Open your OpenWebUI admin panel
- Go to Settings → Pipelines
- Add the endpoint of this service:

```
http://pipelines:9099
```

If OpenWebUI runs in the same Docker network, use `http://pipelines:9099`.
If it runs outside Docker, use `http://<your-server-ip>:9099`.

Once added, the pipeline `ask_wiki` will appear and be callable by the AI.

## 🧪 Example usage
You can now ask:

> "What are the criteria to become a Junior-Enterprise?"

The pipeline will automatically:
- Search in Outline collections and documents
- Retrieve content
- Return the relevant answer

---

## 📦 docker-compose.yml

```yaml
services:
  pipelines:
    image: ghcr.io/open-webui/pipelines:main
    ports:
      - 127.0.0.1:9099:9099
    volumes:
      - ./pipelines:/app/pipelines
    environment:
      PORT: 9099
      PIPELINES_AUTO_IMPORT: true
      OUTLINE_API_BASE: "https://wiki.ject.fr/api"
      OUTLINE_API_TOKEN: "your_outline_api_token_here"

volumes: {}
```

👉 Ce service est autonome. Tu n’as pas besoin d’ajouter openwebui dedans si tu l’as déjà déployé ailleurs (Dokploy, autre repo).
Le but est de déployer uniquement la partie pipelines.

---

## 🛠️ Développement local (optionnel)

Sur Windows (cmd.exe):

```bat
python -m venv .venv
.\.venv\Scripts\activate
python -m pip install -U pip
pip install -r requirements.txt
```

Test rapide:

```bat
python -c "import requests; print(requests.__version__)"
```

Démarrage manuel (par exemple pour tester des appels HTTP vers Outline dans un script local):

```bat
set OUTLINE_API_BASE=https://wiki.ject.fr/api
set OUTLINE_API_TOKEN=your_outline_api_token_here
python .\pipelines\ask_wiki.py
```
