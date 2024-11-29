import streamlit as st


def main():
    st.title("Transaction Categoriser & Aggregator")
    st.write(
        "Upload a CSV file of transactions with columns: `date`, `description`, and `amount`."
    )
    uploaded_file = st.file_uploader("Choose a CSV file", type=["csv"])


if __name__ == "__main__":
    main()
