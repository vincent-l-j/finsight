import streamlit as st
import pandas as pd


def apply_rules(df, description_column, rules):
    """
    Apply user-defined rules to categorize transactions.
    """

    def categorize(description):
        for rule in rules:
            condition, value, category = (
                rule["condition"],
                rule["value"],
                rule["category"],
            )
            if condition == "Starts With" and description.startswith(value):
                return category
            elif condition == "Contains" and value in description:
                return category
            elif condition == "Ends With" and description.endswith(value):
                return category
        return description  # Default to the description if no rule matches

    df["category"] = df[description_column].apply(categorize)
    return df


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

    # Rule-based categorization
    st.write("### Specify Rules for Categorization")
    if "rules" not in st.session_state:
        st.session_state["rules"] = []

    # Add a new rule
    with st.form("add_rule_form"):
        st.write("Add a New Rule")
        condition = st.selectbox("Condition", ["Starts With", "Contains", "Ends With"])
        value = st.text_input("Value")
        category = st.text_input("Category")
        submitted = st.form_submit_button("Add Rule")
        if submitted and value and category:
            st.session_state["rules"].append(
                {"condition": condition, "value": value, "category": category}
            )
            st.success("Rule added!")

    # Display and manage rules
    st.write("### Current Rules")
    show_rules = st.checkbox("Show current rules")
    if show_rules:
        for i, rule in enumerate(st.session_state["rules"]):
            st.write(
                f"{i+1}. If description **{rule['condition']}** '{rule['value']}', categorize as **{rule['category']}**"
            )
            if st.button(f"Remove Rule {i+1}"):
                st.session_state["rules"].pop(i)

    # Apply rules to categorize transactions
    if st.session_state["rules"]:
        df = apply_rules(df, description_column, st.session_state["rules"])
        st.write("### Aggregated by Month and Category")
        df["month"] = df[date_column].dt.to_period("M").astype(str)
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
