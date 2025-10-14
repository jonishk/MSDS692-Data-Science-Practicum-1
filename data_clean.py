import pandas as pd
import re
import matplotlib.pyplot as plt
import seaborn as sns

import sys
sys.stdout.reconfigure(line_buffering=True)


# Load dataset
df = pd.read_csv("reddit_data.csv")

# Drop duplicates by ID (post or comment) or text
df = df.drop_duplicates(subset=["id"], keep="last")
df = df.drop_duplicates(subset=["title", "content"], keep="last")

# Merge title + content into one field
df["full_text"] = df[["title", "content"]].astype(str).agg(" ".join, axis=1)


# Structured domain-specific dictionary
keywords_dict = {
    "Law": {
        "Case Management": ["clio", "filevine", "smokeball", "practicepanther"],
        "Research": ["lexisnexis", "westlaw"],
        "Document Mgmt": ["imanage", "everlaw", "relativity", "document automation"],
        "Payments": ["lawpay"],
        "Other": ["ediscovery", "contract software"]
    },
    "Construction": {
        "Design": ["autocad", "revit", "bim", "sketchup", "solidworks"],
        "Project Mgmt": ["bluebeam", "procore", "plangrid", "primavera", "project management"],
        "Other": ["construction software", "estimating software"]
    },
    "Tech": {
        "DevOps": ["jira", "docker", "kubernetes", "ansible"],
        "Cloud": ["aws", "azure", "gcp"],
        "Security": ["firewall", "endpoint management", "security software"],
        "Infra": ["servicenow", "splunk", "active directory", "linux"]
    }
}

def find_keywords(text, keywords):
    found = [kw for kw in keywords if re.search(rf"\b{re.escape(kw)}\b", text.lower())]
    return found


# Keyword detection by category
df["keywords_found"] = [[] for _ in range(len(df))]
df["software_flag"] = False

for category, subcats in keywords_dict.items():
    mask = df["category"] == category
    for subcat, keywords in subcats.items():
        df.loc[mask, "keywords_found"] = df.loc[mask].apply(
            lambda row: list(set(row["keywords_found"]) | set(find_keywords(str(row["full_text"]), keywords))),
            axis=1
        )

# Flag rows with at least one keyword
df["software_flag"] = df["keywords_found"].apply(lambda x: len(x) > 0)


# Keep only rows with software/tool mentions
df_clean = df[df["software_flag"] == True].copy()


# Clean text for embeddings
def clean_text(text):
    text = str(text).lower()
    text = re.sub(r"http\S+|www\S+", "", text)
    text = re.sub(r"[^a-z\s]", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text

df_clean["clean_text"] = df_clean["full_text"].apply(clean_text)


# Save cleaned dataset + summary
df_clean.to_csv("reddit_data_clean.csv", index=False)

# Flatten keyword mentions for counts
all_keywords = df_clean["keywords_found"].explode()
keyword_counts = all_keywords.value_counts().reset_index()
keyword_counts.columns = ["keyword", "count"]



# EDA Plots
# Plot 1: Mentions per category
plt.figure(figsize=(6, 4))
sns.countplot(data=df_clean, x="category", order=df_clean["category"].value_counts().index, palette="Set2")
plt.title("Software Mentions by Category")
plt.xlabel("Category")
plt.ylabel("Count of Mentions")
plt.show()

# Plot 2: Top Software Mentions
top_keywords = keyword_counts.head(10)
plt.figure(figsize=(8, 5))
sns.barplot(x=top_keywords["count"], y=top_keywords["keyword"], palette="viridis")
plt.title("Top 10 Most Mentioned Tools/Software")
plt.xlabel("Number of Mentions")
plt.ylabel("Software/Tool")
plt.show()

# Plot 3: Subreddit distribution
top_subs = df_clean["subreddit"].value_counts().head(10)
plt.figure(figsize=(8, 5))
sns.barplot(x=top_subs.values, y=top_subs.index, palette="mako")
plt.title("Top 10 Subreddits with Software Mentions")
plt.xlabel("Number of Mentions")
plt.ylabel("Subreddit")
plt.show()

# Plot 4: Time trend of mentions
df_clean["created_utc"] = pd.to_datetime(df_clean["created_utc"], errors="coerce")
df_trend = df_clean.groupby(df_clean["created_utc"].dt.date).size()

plt.figure(figsize=(10, 5))
df_trend.plot(kind="line", marker="o")
plt.title("Trend of Software Mentions Over Time")
plt.xlabel("Date")
plt.ylabel("Number of Mentions")
plt.grid(True)
plt.show()
