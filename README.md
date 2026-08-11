# BeReady

An honest hiking-readiness assistant. You pick a trail, your fitness level, and how many
weeks you have, and BeReady tells you honestly whether you can handle it, and exactly what
to do to prepare. It never invents facts and never gives medical advice.

Built with Streamlit. The readiness logic is deterministic, so the app runs instantly with
no API key.

## Run locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

The app opens at http://localhost:8501.

## Deploy free on Streamlit Community Cloud

1. Create a **public** GitHub repository and add these two files to it: `app.py` and `requirements.txt`.
2. Go to https://share.streamlit.io and sign in with GitHub.
3. Click **New app**, choose your repository, branch `main`, and main file `app.py`.
4. Click **Deploy**. In a minute you get a public URL like `https://bereadyapp.streamlit.app`.

That public URL is what you can screenshot and link in the Behance case study.

## Files

- `app.py` — the Streamlit interface and readiness logic
- `requirements.txt` — dependencies (just `streamlit`)
