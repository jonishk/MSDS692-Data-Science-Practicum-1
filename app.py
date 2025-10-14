from flask import Flask, render_template, request, jsonify, Response
from dotenv import load_dotenv
import subprocess
import json
import sys
import os
import time
import pandas as pd

from langchain_pinecone import PineconeVectorStore
from langchain_openai import ChatOpenAI
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate
from langchain.embeddings import HuggingFaceEmbeddings
from pinecone import Pinecone, ServerlessSpec



# Flask setup
app = Flask(__name__)
load_dotenv()

PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
os.environ["PINECONE_API_KEY"] = PINECONE_API_KEY
os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY


# Embeddings + Pinecone setup
embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-mpnet-base-v2")
index_name = "reddit-insights"

try:
    pc = Pinecone(api_key=PINECONE_API_KEY)
    existing_indexes = [i["name"] for i in pc.list_indexes()]
    if index_name not in existing_indexes:
        print(f"Index '{index_name}' not found. Creating new Pinecone index...")
        pc.create_index(
            name=index_name,
            dimension=768,  # mpnet-base-v2 embedding size
            metric="cosine",
            spec=ServerlessSpec(cloud="aws", region="us-east-1"),
        )
        print(f" Created Pinecone index: {index_name}")
        time.sleep(10)  # allow index to initialize
    else:
        print(f"Connected to existing Pinecone index: {index_name}")

    docsearch = PineconeVectorStore.from_existing_index(
        index_name=index_name,
        embedding=embeddings
    )
except Exception as e:
    print(f" Could not connect to Pinecone: {e}")
    docsearch = None

retriever = None
if docsearch:
    retriever = docsearch.as_retriever(
        search_type="similarity",
        search_kwargs={"k": 10,}
    )


# System prompt
system_prompt = (
    "You are a research assistant summarizing Reddit discussions about software tools "
    "used in Law, Construction, and Tech industries.\n\n"
    "Use the Reddit excerpts below to answer accurately. You may make brief, logical inferences from the context but avoid unsupported assumptions.\n"
    "If the context does not include relevant data, respond with:\n"
    "'I don’t know based on the provided Reddit data.'\n\n"
    "Include subreddit or profession context if available.\n\n"
    "Context:\n{context}"
)

llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0.2, max_tokens=400)
prompt = ChatPromptTemplate.from_messages([("system", system_prompt), ("human", "{input}")])
question_answer_chain = create_stuff_documents_chain(llm, prompt)
rag_chain = create_retrieval_chain(retriever, question_answer_chain) if retriever else None



# PIPELINE STEPS MAP
PIPELINE_STEPS = {
    "collect": "data_collection.py",
    "clean": "data_clean.py",
    "sentiment": "data_sentiment.py",
    "index": "store_index.py",
    "evaluate": "evaluate.py"
}



# Utility: Run scripts with live log streaming
def stream_process(script_path):
    process = subprocess.Popen(
        [sys.executable, "-u", script_path],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
        encoding="utf-8",
        errors="replace"
    )
    for line in iter(process.stdout.readline, ''):
        yield f"data:{line.strip()}\n\n"
    process.stdout.close()
    process.wait()
    yield f"data: Step finished.\n\n"
    yield "event: close\ndata: done\n\n"



# Routes
@app.route("/")
def index():
    return render_template("index.html")


@app.route("/stream/<step>")
def stream_step(step):
    if step not in PIPELINE_STEPS:
        return "Invalid step", 400
    return Response(stream_process(PIPELINE_STEPS[step]), mimetype="text/event-stream")


@app.route("/stream/full")
def stream_full_pipeline():
    def full_run():
        for step, script in PIPELINE_STEPS.items():
            if step == "evaluate":
                continue  # skip evaluation in full run
            yield f"data:===== Starting {step.upper()} =====\n\n"
            for line in stream_process(script):
                yield line
            yield f"data:===== Finished {step.upper()} =====\n\n"
        yield f"data: Full pipeline completed successfully!\n\n"
    return Response(full_run(), mimetype="text/event-stream")


@app.route("/get_evaluation_results")
def get_evaluation_results():
    """Read evaluation_results.csv and return JSON for frontend table."""
    results_path = os.path.abspath("evaluation_results.csv")
    if not os.path.exists(results_path):
        return jsonify({"error": "No evaluation results found. Run evaluation first."}), 404

    try:
        df = pd.read_csv(results_path)
        if df.empty:
            return jsonify({"error": "Evaluation file is empty."}), 404
        # Simplify and rename columns
        rename_map = {
            "question": "question",
            "rag_answer": "rag_answer",
            "llm_only_answer": "llm_answer",
            "rag_relevance": "rag_relevance",
            "llm_relevance": "llm_relevance"
        }
        df.rename(columns=rename_map, inplace=True)
        records = df[["question", "rag_answer", "llm_answer", "rag_relevance", "llm_relevance"]].fillna("").to_dict(orient="records")
        return jsonify(records)
    except Exception as e:
        return jsonify({"error": f"Failed to load evaluation results: {str(e)}"}), 500



# Chatbot endpoint
@app.route("/get", methods=["POST"])
def chat():
    msg = request.form["msg"]

    if not docsearch:
        return " Pinecone index not found. Please run 'Store to Pinecone' step first."

     # --- NEW: category-aware filtering ---
    if "construction" in msg.lower():
        search_filter = {"category": "Construction"}
    elif "law" in msg.lower() or "legal" in msg.lower():
        search_filter = {"category": "Law"}
    elif "tech" in msg.lower() or "software" in msg.lower():
        search_filter = {"category": "Tech"}
    else:
        search_filter = None

    # --- Retrieval ---
    try:
        retrieved_docs_with_scores = docsearch.similarity_search_with_score(
            msg, k=10, filter=search_filter
        )
        relevant_docs = [doc for doc, score in retrieved_docs_with_scores if doc.page_content.strip()]
    except Exception as e:
        return f"Error during retrieval: {e}"

    if not relevant_docs:
        return "I don’t know based on the provided Reddit data."

    response = question_answer_chain.invoke({"input": msg, "context": relevant_docs})
    final_answer = response.strip() if isinstance(response, str) else str(response)

    if not final_answer or "I don’t know" in final_answer:
        return "I don’t know based on the provided Reddit data."
    return final_answer



# Run Flask
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)
