import streamlit as st
import httpx

API_URL = "http://localhost:8000"


def reset_password_simple():
    st.title("Reset Password")

    # Show success message and "Go to Login" button if password just reset
    if st.session_state.get("password_reset_success"):
        st.success("Password reset successfully! Please login with your new password.")
        if st.button("Go to Login"):
            st.session_state.page = "login"
            st.session_state.password_reset_success = False
            st.rerun()
        return  # Stop here, don't show other UI

    # Initialize session state variables
    if "email_verified" not in st.session_state:
        st.session_state.email_verified = False
        st.session_state.email = ""

    # Step 1: Verify email exists
    if not st.session_state.email_verified:
        email = st.text_input("Enter your registered email to reset password")
        if st.button("Verify Email"):
            if not email:
                st.error("Please enter an email address.")
            else:
                try:
                    response = httpx.post(f"{API_URL}/auth/reset-password", json={"email": email}, timeout=10)
                    if response.status_code == 200:
                        st.session_state.email_verified = True
                        st.session_state.email = email
                        st.success("Email verified. You may now set a new password.")
                        st.rerun()
                    else:
                        st.error(response.json().get("detail", "Email not found."))
                except Exception as e:
                    st.error(f"Network error: {str(e)}")

    # Step 2: Enter new password and confirm
    if st.session_state.email_verified:
        new_password = st.text_input("New Password", type="password")
        confirm_password = st.text_input("Confirm New Password", type="password")

        if st.button("Reset Password"):
            if not new_password or not confirm_password:
                st.error("Please enter and confirm your new password.")
            elif new_password != confirm_password:
                st.error("Passwords do not match.")
            else:
                try:
                    payload = {"email": st.session_state.email, "new_password": new_password}
                    response = httpx.post(f"{API_URL}/auth/update-password", json=payload, timeout=10)
                    if response.status_code == 200:
                        st.session_state.password_reset_success = True
                        st.session_state.email_verified = False
                        st.session_state.email = ""
                        st.rerun()
                    else:
                        st.error(response.json().get("detail", "Failed to reset password."))
                except Exception as e:
                    st.error(f"Network error: {str(e)}")


if __name__ == "__main__":
    reset_password_simple()
