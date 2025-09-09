import streamlit as st
import httpx

API_URL = "http://localhost:8000"

def reset_password_with_otp():
    st.title("Reset Password (with OTP)")

    # Initialize session state
    if "step" not in st.session_state:
        st.session_state.step = "email"
        st.session_state.email = ""
        st.session_state.otp = ""

    # Step 1: Enter email and send OTP
    if st.session_state.step == "email":
        email = st.text_input("Enter your registered email")
        if st.button("Send OTP"):
            if not email:
                st.error("Please enter an email address.")
            else:
                try:
                    res = httpx.post(f"{API_URL}/auth/request-password-reset", json={"email": email}, timeout=10)
                    if res.status_code == 200:
                        st.session_state.email = email
                        st.session_state.step = "otp"
                        st.success("OTP sent to your email.")
                        st.rerun()
                    else:
                        st.error(res.json().get("detail", "Failed to send OTP."))
                except Exception as e:
                    st.error(f"Network error: {str(e)}")

    # Step 2: Enter OTP
    elif st.session_state.step == "otp":
        otp = st.text_input("Enter the OTP sent to your email")
        if st.button("Verify OTP"):
            if not otp:
                st.error("Please enter the OTP.")
            else:
                st.session_state.otp = otp
                st.session_state.step = "new_password"
                st.success("OTP verified. Now set your new password.")
                st.rerun()

    # Step 3: Reset password
    elif st.session_state.step == "new_password":
        new_password = st.text_input("New Password", type="password")
        confirm_password = st.text_input("Confirm New Password", type="password")

        if st.button("Reset Password"):
            if not new_password or not confirm_password:
                st.error("Please fill in both password fields.")
            elif new_password != confirm_password:
                st.error("Passwords do not match.")
            else:
                try:
                    payload = {
                        "email": st.session_state.email,
                        "otp": st.session_state.otp,
                        "new_password": new_password
                    }
                    res = httpx.post(f"{API_URL}/auth/verify-otp-and-reset", json=payload, timeout=10)
                    if res.status_code == 200:
                        st.success("Password reset successfully! Please login with your new password.")
                        # reset session state
                        st.session_state.step = "email"
                        st.session_state.email = ""
                        st.session_state.otp = ""
                    else:
                        st.error(res.json().get("detail", "Failed to reset password."))
                except Exception as e:
                    st.error(f"Network error: {str(e)}")

if __name__ == "__main__":
    reset_password_with_otp()
