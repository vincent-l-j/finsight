import streamlit as st
import pandas as pd


def main():
    st.title("Transaction Categoriser & Aggregator")
    st.write(
        "Upload a CSV file of transactions with columns: `date`, `description`, and `amount`."
    )
    uploaded_file = st.file_uploader("Choose a CSV file", type=["csv"])
    if not uploaded_file:
        return
    df = pd.read_csv(uploaded_file)
    st.write(df)


if __name__ == "__main__":
    main()
