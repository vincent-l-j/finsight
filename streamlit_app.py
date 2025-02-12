import re
import streamlit as st
import pandas as pd
from collections import Counter

payment_prefixes = [
    "VISA DEBIT PURCHASE CARD 2543",
    "VISA DEBIT DEPOSIT CARD 2543",
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
    cleaned = re.sub(r"(?<!\d)/", " ", str(text).replace("*", " "))
    is_prefix = True
    while is_prefix:
        is_prefix = False
        for x in payment_prefixes:
            if cleaned.startswith(x):
                cleaned = cleaned.replace(x, "").lstrip()
                is_prefix = True
                break

    return cleaned


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
    is_preview = st.checkbox("Preview Uploaded Data")
    if is_preview:
        st.write("### Preview of Uploaded Data")
        st.write(df)

    # infer the column mapping
    column_names = df.columns.tolist()
    group_words_option = 2
    date_column = "Date"
    date_index = 0
    description_column = "Description"
    description_index = 1
    debit_column = ""
    debit_index = 2
    credit_column = ""
    credit_index = 3
    amount_column = "Amount"
    amount_index = 2
    date_format = ""
    for i, c in enumerate(column_names):
        if c.lower() == "date":
            date_column = c
            date_index = i
        elif c.lower() == "description":
            description_column = c
            description_index = i
        elif "debit" in c.lower():
            debit_column = c
            debit_index = i
        elif "credit" in c.lower():
            credit_column = c
            credit_index = i
        elif "amount" in c.lower():
            amount_column = c
            amount_index = i
    if debit_column and credit_column:
        amount_column = "Amount"
        df[amount_column] = df[credit_column].astype(str).str.replace(",", "").astype(
            float
        ).fillna(0) - df[debit_column].astype(str).str.replace(",", "").astype(
            float
        ).fillna(
            0
        )

    sample_date = df[date_column].iloc[0]
    if len(sample_date) == 10:
        sep_char = sample_date[4]
        if sep_char in ["/", "-", " "]:
            date_format = f"%Y{sep_char}%m{sep_char}%d"
        elif sample_date[2] in ["/", "-", " "]:
            # could also be month day year but ignore the American way
            sep_char = sample_date[2]
            date_format = f"%d{sep_char}%m{sep_char}%Y"
    elif len(sample_date) == 8:
        sep_char = sample_date[2]
        if sep_char in ["/", "-"]:
            date_format = f"%d{sep_char}%m{sep_char}%y"
        else:
            date_format = "%Y%m%d"
    elif len(sample_date) == 11:
        date_format = "%d %b %Y"

    if not date_format:
        raise ValueError(f"Unrecognised date format: {sample_date}")

    is_edit_mapping = st.checkbox("Edit column mapping and settings")
    if is_edit_mapping:
        # Dynamically specify the column names
        st.write("### Specify Column Mapping")

        date_column = st.selectbox(
            "Select the Date Column",
            column_names,
            index=date_index,
        )
        description_column = st.selectbox(
            "Select the Description Column",
            column_names,
            index=description_index,
        )
        amount_option = st.radio(
            "How is the Amount Represented?",
            options=["Single Column", "Split into Debit/Credit"],
            index=1 if debit_column and credit_column else 0,
        )

        amount_column = "amount"
        if amount_option == "Single Column":
            amount_column = st.selectbox(
                "Select the Amount Column",
                column_names,
                index=amount_index,
            )
        else:
            debit_column = st.selectbox(
                "Select the Debit Column", column_names, index=debit_index
            )
            credit_column = st.selectbox(
                "Select the Credit Column", column_names, index=credit_index
            )
            # Combine debit and credit into a single column
            df[amount_column] = df[credit_column].astype(str).str.replace(
                ",", ""
            ).astype(float).fillna(0) - df[debit_column].astype(str).str.replace(
                ",", ""
            ).astype(
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
            index=list(date_formats.values()).index(date_format),
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
    df["month"] = df.apply(
        lambda x: (x["month"] + (" Debit" if x[amount_column] < 0 else " Credit")),
        axis=1,
    )
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
