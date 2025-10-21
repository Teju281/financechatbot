import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from rapidfuzz import fuzz
import os
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet

# -------------------------------
# Page Setup
# -------------------------------
st.set_page_config(page_title="Smart Finance Assistant", page_icon="💰", layout="wide")
DATA_FILE = "transactions.csv"

# -------------------------------
# Helper Functions
# -------------------------------
def load_data():
    if os.path.exists(DATA_FILE):
        return pd.read_csv(DATA_FILE)
    else:
        return pd.DataFrame(columns=["category", "amount"])

def save_data(df):
    df.to_csv(DATA_FILE, index=False)

def generate_pdf_report(income, df):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    elements = []

    elements.append(Paragraph("💰 Monthly Finance Report", styles["Title"]))
    elements.append(Spacer(1, 12))

    total_expense = df["amount"].sum()
    remaining = income - total_expense
    savings = max(0, remaining)

    summary = f"""
    <b>Total Income:</b> ₹{income:.2f}<br/>
    <b>Total Expenses:</b> ₹{total_expense:.2f}<br/>
    <b>Estimated Savings:</b> ₹{savings:.2f}<br/>
    """
    elements.append(Paragraph(summary, styles["Normal"]))
    elements.append(Spacer(1, 12))

    if not df.empty:
        table_data = [["Category", "Amount (₹)"]] + df.values.tolist()
        table = Table(table_data, hAlign="LEFT")
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.lightblue),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
            ("BACKGROUND", (0, 1), (-1, -1), colors.whitesmoke),
            ("GRID", (0, 0), (-1, -1), 1, colors.gray),
        ]))
        elements.append(table)
    else:
        elements.append(Paragraph("No expenses recorded.", styles["Normal"]))

    doc.build(elements)
    buffer.seek(0)
    return buffer

# -------------------------------
# Session Initialization
# -------------------------------
if "income" not in st.session_state:
    st.session_state.income = 0.0
if "transactions" not in st.session_state:
    st.session_state.transactions = load_data().to_dict("records")

# -------------------------------
# UI Header
# -------------------------------
st.markdown("""
<h1 style='text-align:center; color:#2E86C1;'>💬 Smart Personal Finance Assistant</h1>
<p style='text-align:center; font-size:18px; color:gray;'>
Track income, manage expenses, get insights — and download your financial report instantly.
</p>
""", unsafe_allow_html=True)

# -------------------------------
# Step 1: Monthly Income
# -------------------------------
st.subheader("💵 Step 1: Enter Monthly Income")

col1, col2 = st.columns([2, 1])
with col1:
    income = st.number_input("Enter your monthly income (₹)", min_value=0.0, step=500.0, value=st.session_state.income)
with col2:
    if st.button("💾 Save Income"):
        st.session_state.income = income
        st.success(f"Saved monthly income: ₹{income:.2f}")

# -------------------------------
# Step 2: Add Expense
# -------------------------------
st.subheader("💳 Step 2: Add Expenses")

with st.expander("➕ Add a new expense"):
    with st.form("expense_form"):
        c1, c2 = st.columns(2)
        with c1:
            category = st.text_input("Expense Category (e.g., Food, Rent, Travel)")
        with c2:
            amount = st.number_input("Amount (₹)", min_value=0.0, step=10.0)
        add_expense = st.form_submit_button("Add Expense")

        if add_expense and category:
            new_entry = {"category": category.title(), "amount": amount}
            st.session_state.transactions.append(new_entry)
            df = pd.DataFrame(st.session_state.transactions)
            save_data(df)
            st.success(f"✅ Added ₹{amount:.2f} to {category.title()}")

# -------------------------------
# Step 3: AI Chatbot Input
# -------------------------------
st.subheader("🤖 Step 3: Talk to Your Finance Assistant")

user_input = st.text_input("💬 Type (e.g., 'I spent 500 on groceries', 'Show my biggest expense')")

if user_input:
    response = "🤔 I'm not sure I understood that."
    user_lower = user_input.lower()
    df = pd.DataFrame(st.session_state.transactions)

    # NLP Logic
    if "spend" in user_lower or "spent" in user_lower:
        words = user_lower.split()
        try:
            amount = float([w for w in words if w.replace('.', '', 1).isdigit()][0])
            category = next((w for w in words if w.isalpha()), "Miscellaneous")
            new_entry = {"category": category.capitalize(), "amount": amount}
            st.session_state.transactions.append(new_entry)
            df = pd.DataFrame(st.session_state.transactions)
            save_data(df)
            response = f"💸 Added ₹{amount:.2f} to {category.capitalize()} expenses."
        except:
            response = "Please specify a valid amount."

    elif fuzz.partial_ratio(user_lower, "how much did i spend") > 70:
        total = df["amount"].sum()
        response = f"🧾 You've spent ₹{total:.2f} so far this month."

    elif fuzz.partial_ratio(user_lower, "biggest expense") > 70:
        if not df.empty:
            top = df.groupby("category")["amount"].sum().idxmax()
            top_amt = df.groupby("category")["amount"].sum().max()
            response = f"📊 Your biggest expense category is **{top} (₹{top_amt:.2f})**."
        else:
            response = "You haven't added any expenses yet."

    elif fuzz.partial_ratio(user_lower, "savings") > 70:
        total_expense = df["amount"].sum()
        savings = st.session_state.income - total_expense
        response = f"💰 Your estimated savings this month: ₹{savings:.2f}"

    elif "tax" in user_lower:
        try:
            salary = [float(w) for w in user_lower.split() if w.replace('.', '', 1).isdigit()][0]
            tax = salary * 0.05
            response = f"💼 Estimated tax on ₹{salary:.2f} is ₹{tax:.2f} (5% rate)."
        except:
            response = "Please include your income amount to estimate tax."

    st.info(response)

# -------------------------------
# Step 4: Dashboard + Download
# -------------------------------
st.subheader("📊 Step 4: Expense Summary Dashboard")

if st.session_state.transactions:
    df = pd.DataFrame(st.session_state.transactions)
    total_expense = df["amount"].sum()
    remaining = st.session_state.income - total_expense
    savings = max(0, remaining)

    c1, c2, c3 = st.columns(3)
    c1.metric("💵 Total Income", f"₹{st.session_state.income:.2f}")
    c2.metric("💳 Total Expenses", f"₹{total_expense:.2f}")
    c3.metric("💰 Estimated Savings", f"₹{savings:.2f}")

    st.write("### 📘 Expense Details")
    st.dataframe(df)

    col1, col2 = st.columns(2)
    with col1:
        st.write("#### Bar Chart: Expenses by Category")
        fig1, ax1 = plt.subplots()
        df.groupby("category")["amount"].sum().plot(kind="bar", ax=ax1, color="#5DADE2")
        plt.xticks(rotation=45)
        st.pyplot(fig1)

    with col2:
        st.write("#### Pie Chart: Expense Distribution")
        fig2, ax2 = plt.subplots()
        df.groupby("category")["amount"].sum().plot(kind="pie", autopct="%1.1f%%", ax=ax2, startangle=90)
        ax2.set_ylabel("")
        st.pyplot(fig2)

    # -------------------------------
    # Download Section
    # -------------------------------
    st.write("### 📥 Download Your Monthly Report")
    colA, colB = st.columns(2)

    with colA:
        csv_data = df.to_csv(index=False).encode("utf-8")
        st.download_button("⬇️ Download as CSV", data=csv_data, file_name="finance_report.csv", mime="text/csv")

    with colB:
        pdf_buffer = generate_pdf_report(st.session_state.income, df)
        st.download_button("📄 Download as PDF", data=pdf_buffer, file_name="finance_report.pdf", mime="application/pdf")

else:
    st.warning("🚫 No expenses yet! Add some above to view your summary.")
