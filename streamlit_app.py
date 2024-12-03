import streamlit as st
import sqlite3
import altair as alt
import pandas as pd
import requests
from requests.auth import HTTPBasicAuth
import random
import datetime
from oauthlib.oauth2 import WebApplicationClient
from urllib.parse import urlencode
import os

# GitHub OAuth2 credentials
CLIENT_ID = "Ov23licxgATj9XyJQjLx"  # Replace with your GitHub Client ID
CLIENT_SECRET = "319dbe8ad6aec2c1ba9788f67debb9babce5ed41"  # Replace with your GitHub Client Secret
GITHUB_API_URL = "https://api.github.com/user"
REDIRECT_URI = "https://cheat-codes-support-tickets.streamlit.app/callback"  # Corrected Redirect URI


# GitHub OAuth2 client setup
client = WebApplicationClient(CLIENT_ID)

# Set the Streamlit page config
st.set_page_config(page_title="Support Tickets", page_icon="🎫")

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

# GitHub OAuth flow setup
def get_github_login_url():
    authorization_url = f"https://github.com/login/oauth/authorize?client_id={CLIENT_ID}&redirect_uri={REDIRECT_URI}"
    return authorization_url

def get_github_user_data(code):
    token_url = "https://github.com/login/oauth/access_token"
    auth = HTTPBasicAuth(CLIENT_ID, CLIENT_SECRET)
    data = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "code": code,
        "redirect_uri": REDIRECT_URI,
    }
    headers = {
        "Accept": "application/json",
    }

    response = requests.post(token_url, data=data, headers=headers, auth=auth)
    response_data = response.json()
    access_token = response_data["access_token"]

    user_info_response = requests.get(GITHUB_API_URL, headers={"Authorization": f"Bearer {access_token}"})
    user_info = user_info_response.json()

    return user_info

# Streamlit app for login and ticket management
def login_with_github():
    st.title("🎫 Support Tickets - GitHub Login")
    if "code" in st.query_params:  # Updated to use `st.query_params`
        code = st.query_params["code"][0]
        user_data = get_github_user_data(code)
        st.session_state.user_data = user_data
        st.session_state.logged_in = True
        st.success(f"Welcome {user_data['login']}! You are logged in with GitHub.")
    else:
        login_url = get_github_login_url()
        # Center the GitHub button logo using CSS
        st.markdown(
            f'''
            <div style="display: flex; justify-content: center; align-items: center; height: 20vh;">
                <a href="{login_url}" target="_self">
                    <img src="https://github.githubassets.com/images/modules/logos_page/GitHub-Mark.png" width="50" height="50" 
                        style="border: 2px solid white; border-radius: 50%; cursor: pointer;" />
                </a>
            </div>
            ''',
            unsafe_allow_html=True
        )


# Main app logic
if "logged_in" not in st.session_state or not st.session_state.logged_in:
    login_with_github()
else:
    st.title("🎫 Support Tickets")
    st.write("This app allows you to create, view, and manage support tickets. All data is stored in SQLite3.")
    
    # Add a new ticket form
    st.header("Add a New Ticket")
    with st.form("add_ticket_form"):
        issue_description = st.text_input("Issue Description", "")
        priority = st.selectbox("Priority", ["High", "Medium", "Low"])
        submitted = st.form_submit_button("Submit")

        if submitted and issue_description:
            add_ticket(issue_description, priority)
            st.success("Ticket submitted successfully!")

    # Show existing tickets from the database
    st.header("Existing Tickets")
    tickets = fetch_tickets()

    if tickets:
        # Convert the tickets list to a DataFrame for display
        df = pd.DataFrame(tickets, columns=["ID", "Issue", "Status", "Priority", "Date Submitted"])

        # Display tickets in a table with a delete button (bin emoji)
        for index, row in df.iterrows():
            col1, col2, col3, col4, col5, col6 = st.columns([1, 3, 2, 2, 2, 1])
            with col1:
                st.write(row['ID'])
            with col2:
                st.write(row['Issue'])
            with col3:
                st.write(row['Status'])
            with col4:
                st.write(row['Priority'])
            with col5:
                st.write(row['Date Submitted'])
            with col6:
                delete_button = st.button("🗑️", key=row['ID'])

            if delete_button:
                delete_ticket(row['ID'])
                st.success(f"Ticket {row['ID']} deleted successfully!")
                # Refresh tickets after deletion
                st.experimental_rerun()
        
        st.header("Control Centre")
        # Allow users to edit ticket status, priority, and issue description
        edited_df = st.data_editor(
            df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Status": st.column_config.SelectboxColumn(
                    "Status",
                    help="Ticket status",
                    options=["Open", "In Progress", "Closed"],
                    required=True,
                ),
                "Priority": st.column_config.SelectboxColumn(
                    "Priority",
                    help="Ticket priority",
                    options=["High", "Medium", "Low"],
                    required=True,
                ),
                "Issue": st.column_config.TextColumn(
                    "Issue Description",
                    help="Description of the issue",
                    required=True,
                ),
            },
            disabled=["ID", "Date Submitted"],
        )

        # Update the session state tickets list with the edited data
        for index, row in edited_df.iterrows():
            update_ticket(row['ID'], row['Status'], row['Priority'], row['Issue'])

    else:
        st.write("No tickets created yet.")

    # Show statistics
    st.header("Ticket Statistics")
    num_open_tickets = len([ticket for ticket in tickets if ticket[2] == "Open"])
    num_in_progress = len([ticket for ticket in tickets if ticket[2] == "In Progress"])
    num_closed_tickets = len([ticket for ticket in tickets if ticket[2] == "Closed"])

    # Example statistics (can be updated based on actual data)
    first_response_time = 5.2  # Replace with actual first response time calculation
    avg_resolution_time = 16  # Replace with actual average resolution time calculation

    col1, col2, col3 = st.columns(3)
    col1.metric(label="Open Tickets", value=num_open_tickets)
    col2.metric(label="In Progress", value=num_in_progress)
    col3.metric(label="Closed Tickets", value=num_closed_tickets)

    # Add the additional statistics below
    st.write(f"**First Response Time (hours):** {first_response_time}")
    st.write(f"**Average Resolution Time (hours):** {avg_resolution_time}")

    # Only display charts if tickets are available
    if tickets:
        # Fetch updated tickets to refresh DataFrame after edits
        tickets = fetch_tickets()
        df = pd.DataFrame(tickets, columns=["ID", "Issue", "Status", "Priority", "Date Submitted"])

        # Pie chart for status distribution
        status_plot = (
            alt.Chart(df)
            .mark_arc()
            .encode(
                theta=alt.Theta(field="count():Q", type="quantitative"),
                color="Status:N",
                tooltip=["Status:N", "count():Q"],
            )
            .properties(title="Ticket Status Distribution")
        )
        st.altair_chart(status_plot, use_container_width=True)

        # Pie chart for priority distribution
        priority_plot = (
            alt.Chart(df)
            .mark_arc()
            .encode(
                theta=alt.Theta(field="count():Q", type="quantitative"),
                color="Priority:N",
                tooltip=["Priority:N", "count():Q"],
            )
            .properties(title="Ticket Priority Distribution")
        )
        st.altair_chart(priority_plot, use_container_width=True)
