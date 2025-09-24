import os
import re
import requests
import asyncio
import uuid
from playwright.async_api import async_playwright

# mail.tm API base URL
MAILTM_API = "https://api.mail.tm" 

def get_mailtm_token(address, password):
   
    res = requests.post(f"{MAILTM_API}/token", json={
        "address": address,
        "password": password
    })
    res.raise_for_status()
    return res.json()["token"]

async def create_mailtm_inbox():
    res = requests.get(f"{MAILTM_API}/domains")
    res.raise_for_status()
    domain = res.json()["hydra:member"][0]["domain"]

    username = f"{uuid.uuid4().hex[:10]}@{domain}"
    password = uuid.uuid4().hex

    res = requests.post(f"{MAILTM_API}/accounts", json={
        "address": username,
        "password": password
    })
    if res.status_code != 201:
        raise Exception(f"Failed to create mail.tm account: {res.status_code} - {res.text}")

    token = get_mailtm_token(username, password)

    return {
        "email": username,
        "password": password,
        "token": token
    }

async def wait_for_mailtm_email(token, timeout=60):
    headers = {"Authorization": f"Bearer {token}"}
    for _ in range(timeout // 2): 
        try:
            res = requests.get(f"{MAILTM_API}/messages", headers=headers)
            if res.status_code != 200:
                await asyncio.sleep(2)
                continue

            messages = res.json().get("hydra:member", [])
            if not messages:
                await asyncio.sleep(2)
                continue

            # get latest message
            latest = messages[0]
            msg_id = latest["id"]
            msg_res = requests.get(f"{MAILTM_API}/messages/{msg_id}", headers=headers)
            if msg_res.status_code != 200:
                await asyncio.sleep(2)
                continue

            msg_data = msg_res.json()

            body = str(msg_data.get("text", "")) + str(msg_data.get("html", ""))

            match = re.search(r'\b(\d{6})\b', body)
            if match:
                otp = match.group(1)
                print(f"OTP found: {otp}")
                return otp

        except Exception as e:
            print(f"Error checking mail.tm: {e}")

        await asyncio.sleep(2)

    print(" No OTP found in email within timeout.")
    return None

async def main():
    # create mail.tm inbox
    inbox = await create_mailtm_inbox()
    email = inbox["email"]
    token = inbox["token"]
    print(f"Temporary email created: {email}")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()

        # go to signup page
        await page.goto("https://authorized-partner.netlify.app/login  ")
        await page.click("text=Sign Up")

        # agree to terms
        checkbox = page.locator("#remember")
        await checkbox.wait_for(state="visible", timeout=10000)
        await checkbox.click()
        await page.click("text=Continue")

        # Personal details
        phone = f"+1{str(uuid.uuid4().int)[:10]}"
        await page.fill('input[name="firstName"]', "Test")
        await page.fill('input[name="lastName"]', "User")
        await page.fill('input[name="email"]', email)
        await page.fill('input[name="phoneNumber"]', phone)
        await page.fill('input[name="password"]', "Test@1234")
        await page.fill('input[name="confirmPassword"]', "Test@1234")
        await page.click("text=Next")

        # wait for OTP via mail.tm
        print("Waiting for OTP email via mail.tm...")
        otp = await wait_for_mailtm_email(token, timeout=90)  # Increased timeout

        if not otp:
            raise Exception("OTP not received within 90 seconds")

        print(f"OTP received: {otp}")

        # fill OTP
        try:
            otp_input = page.locator("input[data-input-otp='true']")
            await otp_input.wait_for(state="visible", timeout=5000)
            await otp_input.fill(otp)
        except:
            await page.fill("input[maxlength='6']", otp)

        await page.click("text=Verify Code")

        # agency details
        await page.fill('input[name="agency_name"]', "Test Agency")
        await page.fill("input[name='role_in_agency']", "Manager")
        await page.fill("input[name='agency_email']", "demo@example.com")
        await page.fill("input[name='agency_website']", "www.demoagency.com")
        await page.fill("input[name='agency_address']", "123 Demo Street")

        # region dropdown
        combobox = page.locator('button[role="combobox"][aria-haspopup="dialog"]')
        await combobox.click()
        await page.click("text=Nepal")
        await page.click("text=Next")


        # professional experience
        await page.click('button:has-text("Select Your Experience Level")')
        await page.wait_for_timeout(500)
        await page.click('text="5 years" >> visible=true')
        await page.fill("input[name='number_of_students_recruited_annually']", "50")
        await page.fill("input[name='focus_area']", "Undergraduate admissions to Canada")
        await page.fill("input[name='success_metrics']", "90")

        # Services
        await page.click('label:has-text("Career Counseling")')
        await page.click('label:has-text("Admission Applications")')
        await page.click('label:has-text("Visa Processing")')
        await page.click('label:has-text("Test Prepration")')
        await page.click("text=Next")

        # Verification & preferences
        await page.fill("input[name='business_registration_number']", "BRN123456")

        # preferred countries
        combobox = page.locator('button[role="combobox"][aria-haspopup="dialog"]')
        await combobox.click()
        await page.click("text=Canada")

        # institutions
        await page.click('label:has-text("Universities")')
        await page.click('label:has-text("Colleges")')

        # certifications
        await page.fill('input[name="certification_details"]', "ICEF Certified Education Agent")

        # upload files
        file1_path = "example1.pdf"
        file2_path = "example2.pdf"

        for fp in [file1_path, file2_path]:
            if not os.path.exists(fp):
                with open(fp, "wb") as f:
                    f.write(b"%PDF-1.0\n%dummy PDF content for testing\n")
                print(f"Created dummy file: {fp}")

        file_inputs = page.locator('div[role="presentation"] >> input[type="file"]')
        await file_inputs.nth(0).set_input_files(file1_path)
        await file_inputs.nth(1).set_input_files(file2_path)

        # Submit
        await page.click("text=Submit")
        print("Form submitted successfully!")

        await asyncio.sleep(5)
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())