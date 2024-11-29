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
    }
    date_format_readable = st.selectbox(
        "Select Date Format",
        options=date_formats.keys(),
        index=0,
    )
    date_format = date_formats[date_format_readable]

    # Ensure the selected date column is parsed as datetime
    df[date_column] = pd.to_datetime(df[date_column], format=date_format)

    st.write("### Aggregated by Month")
    # Add a 'month' column in "YYYY-MM" format
    month_column = "month"
    df[month_column] = df[date_column].dt.to_period("M").astype(str)
    # Pivot the table to show unique expenses and monthly sums
    pivot_table = df.pivot_table(
        index=description_column,
        columns=month_column,
        values=amount_column,
        aggfunc="sum",
        fill_value=0,
    )
    st.dataframe(pivot_table)


if __name__ == "__main__":
    main()
