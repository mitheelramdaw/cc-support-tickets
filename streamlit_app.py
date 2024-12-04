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

# Create the tickets.db SQLite database and the tickets table
def create_tickets_db():
    conn = sqlite3.connect("tickets.db")
    cursor = conn.cursor()

    # Create the tickets table if it doesn't exist, including StatusUpdated column
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS tickets (
        ID TEXT PRIMARY KEY,
        Issue TEXT NOT NULL,
        Status TEXT NOT NULL,
        Priority TEXT NOT NULL,
        DateSubmitted TEXT NOT NULL,
        StatusUpdated TEXT NOT NULL
    )
    ''')

    conn.commit()
    conn.close()
    print("Database and table created successfully.")

# Function to add a new ticket to the database
def add_ticket(issue_description, priority):
    ticket_id = f"TICKET-{random.randint(1000, 9999)}"
    date_submitted = datetime.datetime.now()
    status = "Open"
    status_updated = date_submitted  # Set status updated time to ticket creation time

    conn = sqlite3.connect("tickets.db")
    cursor = conn.cursor()
    cursor.execute('''
    INSERT INTO tickets (ID, Issue, Status, Priority, DateSubmitted, StatusUpdated)
    VALUES (?, ?, ?, ?, ?, ?)
    ''', (ticket_id, issue_description, status, priority, date_submitted, status_updated))
    conn.commit()
    conn.close()

    # Notify user that the ticket was added
    st.success(f"Ticket {ticket_id} added successfully!")
    st.session_state.refresh_tickets = True  # Refresh the ticket data

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
    status_updated = datetime.datetime.now()  # Update the time when status is changed
    conn = sqlite3.connect("tickets.db")
    cursor = conn.cursor()
    cursor.execute('''
    UPDATE tickets
    SET Status = ?, Priority = ?, Issue = ?, StatusUpdated = ?
    WHERE ID = ?
    ''', (status, priority, issue_description, status_updated, ticket_id))
    conn.commit()
    conn.close()

    # Notify user that the ticket was updated
    st.success(f"Ticket {ticket_id} updated successfully!")
    st.session_state.refresh_tickets = True  # Refresh the ticket data

# Function to delete a ticket from the database by ticket ID or ticket number
def delete_ticket(ticket_identifier):
    conn = sqlite3.connect("tickets.db")
    cursor = conn.cursor()

    # Check if the identifier is a full ticket ID or just a ticket number
    if ticket_identifier.startswith("TICKET-"):
        ticket_id = ticket_identifier
    else:
        ticket_id = f"TICKET-{ticket_identifier}"

    cursor.execute('''
    DELETE FROM tickets WHERE ID = ?
    ''', (ticket_id,))
    conn.commit()
    conn.close()

    # Notify user that the ticket was deleted
    st.success(f"Ticket {ticket_id} deleted successfully!")
    st.session_state.refresh_tickets = True  # Refresh the ticket data

# Function to calculate elapsed time since the ticket was created
def calculate_elapsed_time(status_updated):
    now = datetime.datetime.now()
    elapsed_time = now - status_updated
    days = elapsed_time.days
    hours, remainder = divmod(elapsed_time.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)

    if days > 0:
        return f"{days} day(s), {hours} hour(s)"
    elif hours > 0:
        return f"{hours} hour(s), {minutes} minute(s)"
    else:
        return f"{minutes} minute(s), {seconds} second(s)"

# Initialize Streamlit app
st.set_page_config(page_title="Support Tickets", page_icon="🎫")
st.title("🎫 Support Tickets")
st.write(
    """
    This app allows you to create, view, and manage support tickets. All data is stored in SQLite3.
    """
)

# Sidebar for adding a new ticket (Always visible)
with st.sidebar:
    st.header("Add a New Ticket")
    with st.form("add_ticket_form"):
        issue_description = st.text_area("Issue Description", "")
        priority = st.selectbox("Priority", ["High", "Medium", "Low"])
        submitted = st.form_submit_button("Submit")

        if submitted and issue_description:
            add_ticket(issue_description, priority)
            st.session_state.refresh_tickets = True  # Flag to refresh tickets

# Navigation menu to switch between pages
page = st.sidebar.radio("Select a page", ["Ticket Management", "Visualizations"])

# Ticket Management Page
if page == "Ticket Management":
    st.header("🎫 Ticket Management")
    
    # Fetch tickets on refresh
    if "refresh_tickets" not in st.session_state:
        st.session_state.refresh_tickets = True

    if st.session_state.refresh_tickets:
        tickets = fetch_tickets()
        st.session_state.tickets_df = pd.DataFrame(
            tickets, columns=["ID", "Issue", "Status", "Priority", "Date Submitted", "StatusUpdated"]
        )
        st.session_state.refresh_tickets = False  # Reset the refresh flag

    # Display Existing Tickets
    st.header("Existing Tickets")
    if not st.session_state.tickets_df.empty:
        # Calculate elapsed time for each ticket
        st.session_state.tickets_df["ElapsedTime"] = st.session_state.tickets_df["StatusUpdated"].apply(
            lambda x: calculate_elapsed_time(datetime.datetime.fromisoformat(x))
        )

        st.dataframe(st.session_state.tickets_df, use_container_width=True)
    else:
        st.write("No tickets created yet.")

    # Manage Tickets
    if not st.session_state.tickets_df.empty:
        st.header("Manage Tickets")

        # Create a data editor for ticket management
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
            disabled=["ID", "Date Submitted", "StatusUpdated", "ElapsedTime"],
        )

        # Compare editable_df with the original and update as needed
        for idx, row in editable_df.iterrows():
            if not row.equals(st.session_state.tickets_df.iloc[idx]):
                update_ticket(row["ID"], row["Status"], row["Priority"], row["Issue"])
                st.session_state.refresh_tickets = True  # Refresh the ticket data

        # Add a button to delete tickets
        delete_ticket_id = st.text_input("Ticket ID or Number to delete (e.g., TICKET-1234 or 1234):")
        if st.button("Delete Ticket"):
            if delete_ticket_id:
                delete_ticket(delete_ticket_id)
                st.session_state.refresh_tickets = True  # Refresh the ticket data
            else:
                st.warning("Please provide a valid ticket ID or number to delete.")

# Visualization Page
elif page == "Visualizations":
    st.header("📊 Ticket Visualizations")
    
    # Ticket Statistics
    st.header("Ticket Statistics")
    if "tickets_df" in st.session_state:
        num_open = len(st.session_state.tickets_df[st.session_state.tickets_df["Status"] == "Open"])
        num_in_progress = len(st.session_state.tickets_df[st.session_state.tickets_df["Status"] == "In Progress"])
        num_closed = len(st.session_state.tickets_df[st.session_state.tickets_df["Status"] == "Closed"])

        col1, col2, col3 = st.columns(3)
        col1.metric("Open Tickets", num_open)
        col2.metric("In Progress", num_in_progress)
        col3.metric("Closed Tickets", num_closed)

        # Status Distribution Chart
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

        # Priority Distribution Chart
        st.write("### Ticket Priority Distribution")
        priority_plot = (
            alt.Chart(st.session_state.tickets_df)
            .mark_bar()
            .encode(
                x="Priority:N",
                y="count():Q",
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

