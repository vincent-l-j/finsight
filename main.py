import streamlit as st
import pandas as pd


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
        amount_column = st.selectbox("Select the Amount Column", column_names)
    else:
        debit_column = st.selectbox("Select the Debit Column", column_names)
        credit_column = st.selectbox("Select the Credit Column", column_names)
        # Combine debit and credit into a single column
        df[amount_column] = df[credit_column].fillna(0) - df[debit_column].fillna(0)

    # Ensure the selected date column is parsed as datetime
    df[date_column] = pd.to_datetime(df[date_column], errors="coerce")

    # Preview the processed data
    st.write("### Processed Data")
    st.dataframe(df[[date_column, description_column, amount_column]])

    st.write("The data is now ready for further processing!")


if __name__ == "__main__":
    main()
