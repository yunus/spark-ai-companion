# AI Companion

## Setup:
```sh
# create venv envitonment
python3 -m venv .venv

pip install -r requirements.txt

```

Create API key from AI studio and set it inside `.env` file


```sh
# Runt the code:
uvicorn main:app --reload

# navigate in your browser to localhost:8000
```