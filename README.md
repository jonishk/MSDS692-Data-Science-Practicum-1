# Reddit Insights Chatbot with RAG

## Project Overview

This project aims to build a research tool that uses Reddit discussions to surface industry-specific insights, particularly about commonly used software and related pain points in law firms, construction, and tech. Posts and comments are scraped from selected subreddits, cleaned, and analyzed for software/tool mentions. A Retrieval-Augmented Generation (RAG) chatbot will later be developed so users can query insights conversationally. The project also compares RAG performance with an LLM-only baseline.

Key Features:

- Reddit Data Collection: Scrapes thousands of posts from selected subreddits using the Pushshift API

- Data Cleaning & Filtering: Removes duplicates, irrelevant text, and short posts

- Sentiment Analysis: Uses VADER sentiment scoring to analyze tone around each tool

- RAG Chatbot: Combines a retrieval pipeline (Pinecone + HuggingFace embeddings) with OpenAI GPT-3.5-turbo for grounded answers

- Evaluation System: Compares RAG vs LLM-only accuracy using precision, recall, and F1-score

- Flask Web App: Interactive dashboard with progress logs and chatbot interface

Project Structure
├── app.py                     # Flask web app for chatbot and pipeline
├── evaluate.py                # Script for model evaluation (RAG vs LLM)
├── data_collection.py         # Reddit data scraping
├── data_clean.py              # Cleaning and preprocessing
├── data_sentiment.py          # Sentiment analysis
├── store_index.py             # Create Pinecone index
├── static/                    # CSS and JS files
│   ├── style.css
│   └── script.js
├── templates/
│   └── index.html             # Web interface
├── questions.json             # Evaluation question set
├── requirements.txt           # Python dependencies
├── .env                       # API keys (OpenAI, Pinecone)
└── README.md

# Installation & Setup

# STEPS 01- Clone the repository:

Clone the repository

```bash
git clone https://github.com/jonishk/MSDS692-Data-Science-Practicum-1
cd reddit-insights-chatbot

```

### STEP 02- Create a conda environment after opening the repository

```bash
conda create -n reditbot python=3.10.18 -y
````
```bash
conda activate reditbot
````

### STEP 03- Install dependencies
```bash
pip install -r requirements.txt
```
### STEP 04- Set up environment variables:
Create a .env file with your API keys:
```bash
OPENAI_API_KEY=your_openai_api_key
PINECONE_API_KEY=your_pinecone_api_key

```
### STEP 04 - run the app using app.py
```bash
python app.py
```
### STEP 05 - on your browser run:
```bash
http://localhost:8080
```


