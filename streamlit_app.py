import requests
import streamlit as st

# Replace these with your actual values
CLIENT_ID = 'your-client-id'
CLIENT_SECRET = 'your-client-secret'
REDIRECT_URI = 'https://your-callback-url.com'  # Your GitHub OAuth callback URL
GITHUB_API_URL = 'https://api.github.com/user'

# GitHub OAuth Token URL
TOKEN_URL = 'https://github.com/login/oauth/access_token'

# Function to get user data after OAuth authorization
def get_github_user_data(code):
    # Prepare data for token exchange
    data = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "code": code,
        "redirect_uri": REDIRECT_URI
    }

    # Headers for the request
    headers = {
        "Accept": "application/json"
    }

    # Make the request to exchange the code for an access token
    response = requests.post(TOKEN_URL, data=data, headers=headers)

    # Parse the JSON response
    response_data = response.json()

    # Log the raw response to inspect what GitHub is returning
    print("GitHub Response Data:", response_data)

    # Check if 'access_token' is present in the response
    if "access_token" in response_data:
        access_token = response_data["access_token"]
        # Use the access token to get user info from GitHub
        user_info_response = requests.get(GITHUB_API_URL, headers={"Authorization": f"token {access_token}"})
        user_info = user_info_response.json()

        # Return the user data (e.g., login, email, etc.)
        return user_info
    else:
        # If no access token is found, check for an error and log it
        if "error" in response_data:
            print(f"OAuth Error: {response_data['error_description']}")
            # Handle error based on the error type
            return None
        else:
            print("Unexpected response from GitHub:", response_data)
            return None

# Streamlit logic for handling login
def login_with_github():
    st.title("🎫 Support Tickets - GitHub Login")

    if "code" in st.query_params:  # Check if 'code' parameter is in the URL
        code = st.query_params["code"][0]  # Get the code parameter

        # Get the GitHub user data using the code
        user_data = get_github_user_data(code)

        if user_data:
            # Store user data and login state in session
            st.session_state.user_data = user_data
            st.session_state.logged_in = True
            st.success(f"Welcome {user_data['login']}! You are logged in with GitHub.")
        else:
            st.error("There was an error logging you in with GitHub.")
    else:
        st.write("Please log in using GitHub.")

# Main app logic
if "logged_in" not in st.session_state or not st.session_state.logged_in:
    # Show the login page if the user is not logged in
    login_with_github()
else:
    st.title("🎫 Support Tickets")
    st.write("This app allows you to create, view, and manage support tickets.")
    # Add other dashboard content here
