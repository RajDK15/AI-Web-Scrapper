import time
import streamlit as st
import sqlite3
from datetime import datetime
from scrape import (scrape_website, split_dom_content, clean_body_content, extract_body_content)
from parse import parse_with_ollama

# Set up SQLite Database
conn = sqlite3.connect('users.db', check_same_thread=False)
c = conn.cursor()

# Create Tables for Users and Search History
c.execute('''CREATE TABLE IF NOT EXISTS users
             (username TEXT, password TEXT)''')

c.execute('''CREATE TABLE IF NOT EXISTS search_history
             (username TEXT, search_url TEXT, search_date TEXT)''')

conn.commit()

# Helper Functions
def register_user(username, password):
    c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
    conn.commit()

def login_user(username, password):
    c.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username, password))
    return c.fetchone()

def add_search_history(username, search_url):
    c.execute("INSERT INTO search_history (username, search_url, search_date) VALUES (?, ?, ?)",
              (username, search_url, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit()

def get_search_history(username):
    c.execute("SELECT search_url, search_date FROM search_history WHERE username = ? ORDER BY search_date DESC LIMIT 5", (username,))
    return c.fetchall()

# Streamlit UI for Login/Register
st.title("AI Web Scraper - Login/Register")

menu = ["Login", "Register"]
choice = st.sidebar.selectbox("Menu", menu)

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

if 'username' not in st.session_state:
    st.session_state.username = ""

if choice == "Register":
    st.subheader("Create New Account")
    new_user = st.text_input("Username")
    new_password = st.text_input("Password", type='password')

    if st.button("Register"):
        register_user(new_user, new_password)
        st.success("You have successfully registered!")
        st.info("Go to Login to access your account.")

elif choice == "Login":
    st.subheader("Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type='password')

    if st.button("Login"):
        result = login_user(username, password)
        if result:
            st.session_state.logged_in = True
            st.session_state.username = username
            st.success(f"Welcome, {username}!")
        else:
            st.error("Incorrect Username/Password.")

# Scraper functionality only if logged in
if st.session_state.logged_in:
    st.subheader(f"Logged in as {st.session_state.username}")

    # Sidebar with additional settings
    with st.sidebar:
        st.header("Settings")
        scrape_depth = st.slider("Select scrape depth", 1, 10, 5)
        display_raw_html = st.checkbox("Display raw HTML")

    # Main UI
    st.title("AI Web Scraper")

    url = st.text_input("Enter a Website URL of your choice:", placeholder="e.g., https://example.com")

    # Scrape website button
    if st.button("Scrape site 🚀"):
        if url:
            # Scraping spinner and progress bar
            with st.spinner('Scraping in progress...'):
                progress_bar = st.progress(0)

                # Simulate the scraping process (progress bar demonstration)
                for i in range(100):
                    progress_bar.progress(i + 1)
                    time.sleep(0.05)

                # Actual scraping process
                result = scrape_website(url)
                body_content = extract_body_content(result)
                cleaned_content = clean_body_content(body_content)

                st.session_state.dom_content = cleaned_content

                # Add search history
                add_search_history(st.session_state.username, url)

            # Scraping completed message
            st.success('Scraping completed!')

            # Display detailed results inside an expander
            with st.expander("View Detailed Results"):
                st.write(cleaned_content)

            # Markdown output with URL and scraped data details
            st.markdown("### AI Web Scraper Result")
            st.markdown(f"**URL Scraped:** {url}")
            st.markdown("#### Scraped Data:")

            # Display DOM Content (conditionally show raw HTML)
            if display_raw_html:
                st.text_area("Raw HTML", result, height=300)
            else:
                st.text_area("DOM Content", cleaned_content, height=300)

            # Download button to download the scraped content as a .txt file
            st.download_button(
                label="Download Data",
                data=cleaned_content,
                file_name="scraped_data.txt",
                mime="text/plain",
            )
        else:
            st.error("Please enter a valid URL.")

    # Parsing the scraped content
    if "dom_content" in st.session_state:
        parse_description = st.text_area("Let us know what you want to parse?")

        if st.button("Parse Content"):
            if parse_description:
                st.write("Analyzing the content")

                # Splitting DOM content into chunks and parsing
                dom_chunks = split_dom_content(st.session_state.dom_content)
                result = parse_with_ollama(dom_chunks, parse_description)

                # Display parsed result
                st.write(result)

    # Search History Section
    st.subheader("Your Latest Search History")
    history = get_search_history(st.session_state.username)

    if history:
        for i, (search_url, search_date) in enumerate(history, start=1):
            st.write(f"{i}. **URL:** {search_url} | **Date:** {search_date}")
    else:
        st.info("No search history yet.")
