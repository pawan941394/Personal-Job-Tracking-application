import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore, auth
import pandas as pd
import genai
import datetime


firebase_secrets = {
    "type": st.secrets["firebase"]["type"],
    "project_id": st.secrets["firebase"]["project_id"],
    "private_key_id": st.secrets["firebase"]["private_key_id"],
    "private_key": st.secrets["firebase"]["private_key"].replace('\\n', '\n'),  # Ensure the private key is properly formatted
    "client_email": st.secrets["firebase"]["client_email"],
    "client_id": st.secrets["firebase"]["client_id"],
    "auth_uri": st.secrets["firebase"]["auth_uri"],
    "token_uri": st.secrets["firebase"]["token_uri"],
    "auth_provider_x509_cert_url": st.secrets["firebase"]["auth_provider_x509_cert_url"],
    "client_x509_cert_url": st.secrets["firebase"]["client_x509_cert_url"]
}
# Initialize Firebase Admin SDK (ensure it only initializes once)
if not firebase_admin._apps:
    cred = credentials.Certificate(firebase_secrets)
    firebase_admin.initialize_app(cred)

# Connect to Firestore
db = firestore.client()

# Streamlit app
st.title("Job Tracking APP 💼")

def login():
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        try:
            user = auth.get_user_by_email(email)
            # Note: Direct password verification is not supported in Firebase Admin SDK
            st.session_state['user'] = user
            st.session_state['logged_in'] = True
            st.session_state['show_login'] = False
            st.success("Logged in successfully!")
        except Exception as e:
            st.error(f"Login failed: {e}")

def logout():
    st.session_state['user'] = None
    st.session_state['logged_in'] = False
    st.session_state['show_login'] = True
    st.success("Logged out successfully")

# Initialize session state
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
if 'show_login' not in st.session_state:
    st.session_state['show_login'] = True

# Display login or main content based on the session state
if st.session_state['logged_in']:
    st.sidebar.button("Logout", on_click=logout)

    # Fetch records from Firestore
    docs = db.collection('Followups').stream()
    records = [doc.to_dict() for doc in docs]
    df = pd.DataFrame(records)

    # Initialize session state for the buttons
    if 'show_form' not in st.session_state:
        st.session_state['show_form'] = False
    if 'show_records' not in st.session_state:
        st.session_state['show_records'] = False

    # Create buttons in a row
    col1, col2, col3 = st.columns(3)

    # Handle "Add Followup" button
    with col1:
        if st.button("Add Followup"):
            st.session_state['show_form'] = True
            st.session_state['show_records'] = False

    # Handle "AI Prompt" button
    with col2:
        if st.button("AI Prompt"):
            st.session_state['show_records'] = True
            st.session_state['show_form'] = False

    # Handle "Today" button
    with col3:
        if st.button("Today"):
            st.session_state['show_records'] = False
            st.session_state['show_form'] = False

    # Show form only if "Add Followup" button is clicked
    if st.session_state['show_form']:
        with st.form(key='followups_form'):
            st.markdown("""
                <div style="text-align: center; font-size:50px;" >
                    👤 
                </div>
                """, unsafe_allow_html=True)
            name = st.text_input("Name")
            company = st.text_input("Company")
            email = st.text_input("Email")
            phone = st.text_input("Phone")
            date = st.date_input("Date")
            followup_input = st.text_input("FollowUp")
            comments = st.text_input("Comments")
            
            submit_button = st.form_submit_button('Add')

        if submit_button:
            try:
                db.collection('Followups').document(f'{name} - {company}').set({
                    'name': name,
                    'company': company,
                    'email': email,
                    'phone': phone,
                    'date': str(date),
                    'followup': followup_input,
                    'comments': comments,
                })
                st.success('Data successfully added to Firebase!')
                st.session_state['show_form'] = False
            except Exception as e:
                st.error(f'Error adding data: {e}')

    # Show all follow-up records if "AI Prompt" button is clicked
    if st.session_state['show_records']:
        prompt = st.text_input('Enter your prompt')
        if prompt:
            df['date'] = pd.to_datetime(df['date'], format='%Y-%m-%d')
            ans = genai.gen_ai(df, prompt)
            lis = list(ans['output'].split("&"))[1:]
            count = 1
            for i in lis:
                st.write(f'🏢 {count}')
                st.success(i)
                count += 1

    # Show records for selected date if no other buttons are clicked
    if not st.session_state['show_form'] and not st.session_state['show_records']:
        today_date = str(datetime.datetime.now().date())
        dt_inp = st.date_input('Select Date', value=datetime.datetime.now().date())
        if dt_inp:
            today_date = str(dt_inp)
        today = df[df['date'] == today_date]
        
        if today.empty:
            st.warning("No Records Available For This Date")
        else:
            for i in range(len(today)):
                dic = dict(today.iloc[i])
                st.success(f'🏢 {i+1}')
                st.markdown(f"""
                    **Name**  : {dic["name"]}\n
                    **Company**  : {dic["company"]}\n
                    **Email**  : {dic["email"]}\n
                    **Phone**  : {dic["phone"]}\n
                    **Date**  : {dic["date"]}\n
                    **Followup**  : {dic["followup"]}\n
                    **Comments**  : {dic["comments"]}\n
                    """)

else:
    login()
