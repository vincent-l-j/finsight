import streamlit as st
import pandas as pd
from collections import Counter

payment_prefixes = [
    "EFTPOS",
    "EZI",
    "IPY",
    "LS",
    "LSP",
    "PAYPAL",
    "SMP",
    "SP",
    "SQ",
    "SSP",
    "ZLR",
]


def clean_description(text: str) -> str:
    words = text.replace("*", " ").replace("/", " ").split()
    while words[0] in payment_prefixes:
        words = words[1:]
    return " ".join(words)


def consolidate_words(word_list):
    """
    Consolidate words with different casing.
    Keeps the word that occurs the most, with a tie-breaking preference for more capital letters.
    """
    # Group words by their lowercase version
    word_groups = {}
    for word in word_list:
        normalized = word.lower()
        if normalized not in word_groups:
            word_groups[normalized] = []
        word_groups[normalized].append(word)

    # Determine the best word for each group
    consolidated_words = {}
    for normalized, words in word_groups.items():
        # Count occurrences of each original word
        word_counts = Counter(words)
        # Sort by frequency and then by number of uppercase letters
        best_word = max(
            word_counts,
            key=lambda w: (word_counts[w], sum(1 for c in w if c.isupper())),
        )
        consolidated_words[best_word.lower()] = best_word

    return consolidated_words


def normalise_phrases(phrases: list) -> str:
    lowered = [x.lower().split() for x in phrases]
    # find all common words
    common_words = set(lowered[0]).intersection(*lowered[1:])
    # remove non-common words
    common_phrases = [
        [word for word in lst if word.lower() in common_words]
        for lst in [x.split() for x in phrases]
    ]
    # calculate most common spelling casing of each word
    best_spelling = consolidate_words([y for x in common_phrases for y in x])
    # replace with best spelling
    best_phrases = [
        [best_spelling[word.lower()] for word in lst] for lst in common_phrases
    ]
    # use shortest phrase
    lengths = [len(x) for x in common_phrases]
    # find first min
    idx = lengths.index(min(lengths))
    # create best phrase
    best_phrase = " ".join(best_phrases[idx])
    return best_phrase


def main():
    st.title("Transaction Categoriser & Aggregator")
    st.write(
        "Upload a CSV file of transactions with columns: `date`, `description`, and `amount`."
    )

    # File uploader
    uploaded_file = st.file_uploader("Choose a CSV file", type=["csv"])
    if not uploaded_file:
        return

    # Read the CSV into a DataFrame
    df = pd.read_csv(uploaded_file)
    st.write("### Preview of Uploaded Data")
    st.write(df)

    # Dynamically specify the column names
    st.write("### Specify Column Mapping")
    column_names = df.columns.tolist()

    date_column = st.selectbox(
        "Select the Date Column",
        column_names,
        index=0,
    )
    description_column = st.selectbox(
        "Select the Description Column",
        column_names,
        index=1,
    )
    amount_option = st.radio(
        "How is the Amount Represented?",
        options=["Single Column", "Split into Debit/Credit"],
    )

    amount_column = "amount"
    if amount_option == "Single Column":
        amount_column = st.selectbox(
            "Select the Amount Column",
            column_names,
            index=2,
        )
    else:
        debit_column = st.selectbox("Select the Debit Column", column_names, index=2)
        credit_column = st.selectbox("Select the Credit Column", column_names, index=3)
        # Combine debit and credit into a single column
        df[amount_column] = df[credit_column].astype(str).str.replace(",", "").astype(
            float
        ).fillna(0) - df[debit_column].astype(str).str.replace(",", "").astype(
            float
        ).fillna(
            0
        )

    st.write("### Specify Date Format")
    date_formats = {
        "DD/MM/YYYY": "%d/%m/%Y",
        "MM/DD/YYYY": "%m/%d/%Y",
        "DD-MM-YYYY": "%d-%m-%Y",
        "MM-DD-YYYY": "%m-%d-%Y",
        "DD/MM/YY": "%d/%m/%y",
        "MM/DD/YY": "%m/%d/%y",
        "DD-MM-YY": "%d-%m-%y",
        "MM-DD-YY": "%m-%d-%y",
        "YYYYMMDD": "%Y%m%d",
        "YYYY-MM-DD": "%Y-%m-%d",
        "YYYY/MM/DD": "%Y/%m/%d",
        "DD MMM YYYY": "%d %b %Y",
    }
    date_format_readable = st.selectbox(
        "Select Date Format",
        options=date_formats.keys(),
        index=0,
    )
    date_format = date_formats[date_format_readable]
    st.write("### Description Grouping")
    group_words_option = st.radio(
        "Group descriptions by the first how many words?",
        options=[1, 2, 3],
    )

    # Ensure the selected date column is parsed as datetime
    df[date_column] = pd.to_datetime(df[date_column], format=date_format)

    st.write("### Aggregated by Month and Category")
    df["month"] = df[date_column].dt.to_period("M").astype(str)
    # Apply rules to categorize transactions
    # remove payment prefixes
    df["category"] = df[description_column].apply(clean_description)
    # if they start with the same first two words, group them together
    df["normalised"] = df["category"].str.lower().str.split()
    df["first"] = df["normalised"].apply(lambda x: " ".join(x[:group_words_option]))
    # normalise the phrases
    dict_phrases = df.groupby("first")["category"].agg(normalise_phrases).to_dict()
    # update the category
    df["category"] = df["first"].map(dict_phrases)
    summary = (
        df.groupby(["category", "month"])[amount_column].sum().unstack(fill_value=0)
    )
    st.dataframe(summary)

    # Download the results
    csv = summary.reset_index().to_csv(index=False)
    st.download_button(
        "Download Aggregated Results as CSV",
        csv,
        "aggregated_results.csv",
        "text/csv",
    )


if __name__ == "__main__":
    main()
