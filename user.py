import datetime
import random
import sqlite3
import altair as alt
import pandas as pd
import streamlit as st

# Define color palette for consistent chart coloring
status_colors = {
    "Open": "#1f77b4",  # Blue
    "In Progress": "#ff7f0e",  # Orange
    "Closed": "#2ca02c",  # Green
}

priority_colors = {
    "High": "#d62728",  # Red
    "Medium": "#ff7f0e",  # Orange
    "Low": "#1f77b4",  # Blue
}

# Function to add a new ticket to the database
def add_ticket(issue_description, priority):
    ticket_id = f"TICKET-{random.randint(1000, 9999)}"
    date_submitted = datetime.datetime.now().strftime("%m-%d-%Y")
    status = "Open"

    conn = sqlite3.connect("tickets.db")
    cursor = conn.cursor()
    cursor.execute('''
    INSERT INTO tickets (ID, Issue, Status, Priority, DateSubmitted)
    VALUES (?, ?, ?, ?, ?)
    ''', (ticket_id, issue_description, status, priority, date_submitted))
    conn.commit()
    conn.close()

# Function to fetch all tickets from the database
def fetch_tickets():
    conn = sqlite3.connect("tickets.db")
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM tickets')
    tickets = cursor.fetchall()
    conn.close()
    return tickets

# Function to update ticket status, priority, and issue description in the database
def update_ticket(ticket_id, status, priority, issue_description):
    conn = sqlite3.connect("tickets.db")
    cursor = conn.cursor()
    cursor.execute('''
    UPDATE tickets
    SET Status = ?, Priority = ?, Issue = ?
    WHERE ID = ?
    ''', (status, priority, issue_description, ticket_id))
    conn.commit()
    conn.close()

# Function to delete a ticket from the database
def delete_ticket(ticket_id):
    conn = sqlite3.connect("tickets.db")
    cursor = conn.cursor()
    cursor.execute('''
    DELETE FROM tickets WHERE ID = ?
    ''', (ticket_id,))
    conn.commit()
    conn.close()

# Initialize Streamlit app
st.set_page_config(page_title="Support Tickets", page_icon="🎫")
st.title("🎫 Support Tickets")
st.write(
    """
    This app allows you to create, view, and manage support tickets. All data is stored in SQLite3.
    You can create a ticket, update the ticket status, and view the statistics.
    """
)

# Add a new ticket form
st.header("Add a New Ticket")
with st.form("add_ticket_form"):
    issue_description = st.text_input("Issue Description", "")
    priority = st.selectbox("Priority", ["High", "Medium", "Low"])
    submitted = st.form_submit_button("Submit")

    if submitted and issue_description:
        add_ticket(issue_description, priority)
        st.success("Ticket submitted successfully!")
        st.session_state.refresh_tickets = True  # Flag to refresh tickets

# Fetch all tickets
if "refresh_tickets" not in st.session_state:
    st.session_state.refresh_tickets = True

if st.session_state.refresh_tickets:
    tickets = fetch_tickets()
    st.session_state.tickets_df = pd.DataFrame(
        tickets, columns=["ID", "Issue", "Status", "Priority", "Date Submitted"]
    )
    st.session_state.refresh_tickets = False

# Display Existing Tickets Section
st.header("Existing Tickets")
if not st.session_state.tickets_df.empty:
    st.write("### View All Tickets")
    st.dataframe(st.session_state.tickets_df, use_container_width=True)
else:
    st.write("No tickets created yet.")

# Display Control Center Section
st.header("Control Center")
if not st.session_state.tickets_df.empty:
    st.write("### Manage Tickets")
    editable_df = st.data_editor(
        st.session_state.tickets_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Status": st.column_config.SelectboxColumn(
                "Status",
                options=["Open", "In Progress", "Closed"],
                required=True,
            ),
            "Priority": st.column_config.SelectboxColumn(
                "Priority",
                options=["High", "Medium", "Low"],
                required=True,
            ),
            "Issue": st.column_config.TextColumn(
                "Issue Description",
                required=True,
            ),
        },
        disabled=["ID", "Date Submitted"],
    )

    # Compare editable_df with the original and update as needed
    for idx, row in editable_df.iterrows():
        if not row.equals(st.session_state.tickets_df.iloc[idx]):
            update_ticket(row["ID"], row["Status"], row["Priority"], row["Issue"])
            st.session_state.refresh_tickets = True
else:
    st.write("No tickets available to manage.")

# Display Ticket Statistics
st.header("Ticket Statistics")
num_open_tickets = len(
    st.session_state.tickets_df[
        st.session_state.tickets_df["Status"] == "Open"
    ]
)
num_in_progress = len(
    st.session_state.tickets_df[
        st.session_state.tickets_df["Status"] == "In Progress"
    ]
)
num_closed_tickets = len(
    st.session_state.tickets_df[
        st.session_state.tickets_df["Status"] == "Closed"
    ]
)

col1, col2, col3 = st.columns(3)
col1.metric(label="Open Tickets", value=num_open_tickets)
col2.metric(label="In Progress", value=num_in_progress)
col3.metric(label="Closed Tickets", value=num_closed_tickets)

# Charts Section
st.write("### Ticket Status Distribution")
status_plot = (
    alt.Chart(st.session_state.tickets_df)
    .mark_bar()
    .encode(
        x="Status:N",
        y="count():Q",
        color=alt.Color(
            "Status:N",
            scale=alt.Scale(
                domain=["Open", "In Progress", "Closed"],
                range=[
                    status_colors["Open"],
                    status_colors["In Progress"],
                    status_colors["Closed"],
                ],
            ),
        ),
    )
)
st.altair_chart(status_plot, use_container_width=True)

st.write("### Ticket Priority Distribution")
priority_plot = (
    alt.Chart(st.session_state.tickets_df)
    .mark_arc()
    .encode(
        theta="count():Q",
        color=alt.Color(
            "Priority:N",
            scale=alt.Scale(
                domain=["High", "Medium", "Low"],
                range=[
                    priority_colors["High"],
                    priority_colors["Medium"],
                    priority_colors["Low"],
                ],
            ),
        ),
    )
)
st.altair_chart(priority_plot, use_container_width=True)