import pandas as pd
import re
import matplotlib.pyplot as plt
import seaborn as sns
from nltk.corpus import stopwords
from nltk import word_tokenize, bigrams
from nltk.sentiment import SentimentIntensityAnalyzer
from collections import Counter
import nltk

import sys
sys.stdout.reconfigure(line_buffering=True)


# Setup
nltk.download("vader_lexicon")
nltk.download("punkt")
nltk.download("stopwords")

stop_words = set(stopwords.words("english"))
sia = SentimentIntensityAnalyzer()


# Load dataset
df_clean = pd.read_csv("reddit_data_clean.csv")


# Fix: remove literal "nan" word, not drop rows
def clean_nan_words(text):
    text = str(text).lower()
    text = text.replace("nan ", "").replace(" nan", "").strip()
    return text

df_clean["clean_text"] = df_clean["clean_text"].apply(clean_nan_words)


# Sentiment Analysis
def get_sentiment(text):
    score = sia.polarity_scores(str(text))["compound"]
    if score > 0.05:
        return "positive"
    elif score < -0.05:
        return "negative"
    else:
        return "neutral"

df_clean["sentiment"] = df_clean["clean_text"].apply(get_sentiment)


# Stopword cleanup for pain points
def preprocess_for_painpoints(text):
    tokens = word_tokenize(str(text).lower())
    tokens = [t for t in tokens if t.isalpha() and t not in stop_words]
    return tokens

df_clean["tokens"] = df_clean["clean_text"].apply(preprocess_for_painpoints)


# Pain point extraction (negative posts only)
negative_texts = df_clean[df_clean["sentiment"] == "negative"]

# Unigrams
all_unigrams = [tok for tokens in negative_texts["tokens"] for tok in tokens]
unigram_counts = Counter(all_unigrams).most_common(20)

# Bigrams
all_bigrams = [bg for tokens in negative_texts["tokens"] for bg in bigrams(tokens)]
bigram_counts = Counter(all_bigrams).most_common(20)


columns_to_keep = ["id", "category", "subreddit", "full_text", 
                   "keywords_found", "clean_text", "sentiment"]

df_final = df_clean[columns_to_keep].copy()
df_final.to_csv("reddit_data_sentiment.csv", index=False)

print(f"Saved cleaned + sentiment dataset with {len(df_final)} rows to reddit_data_sentiment.csv")


# Summary Outputs
print("\nSentiment distribution:")
print(df_final["sentiment"].value_counts())

print("\nTop words in negative mentions (after stopword removal):")
print(pd.DataFrame(unigram_counts, columns=["word", "count"]))

print("\nTop bigrams in negative mentions:")
print(pd.DataFrame(bigram_counts, columns=["bigram", "count"]))

# Sentiment Distribution Pie Chart
df_final["sentiment"].value_counts().plot(kind="pie", autopct='%1.2f%%')
plt.title("Sentiment Distribution")
plt.ylabel("")
plt.show()