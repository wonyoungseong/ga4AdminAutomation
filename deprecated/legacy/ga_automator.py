import asyncio
import json
import os
import sys
import re
from playwright.async_api import async_playwright, expect

# Define the path for the persistent browser context
USER_DATA_DIR = "playwright_user_data"

async def run_ga_automation():
    """
    Main function to automate adding a user to a GA4 property using a persistent context.
    """
    # Load configuration from config.json
    try:
        with open('config.json', 'r') as f:
            config = json.load(f)
    except FileNotFoundError:
        print("❌ Error: config.json not found. Please ensure the file exists.")
        return

    account_id = config.get('account_id')
    property_id = config.get('property_id')
    new_user_email = config.get('new_user_email')
    new_user_role = config.get('new_user_role', 'Analyst') # Default to Analyst

    if not all([account_id, property_id, new_user_email]):
        print("❌ Error: Missing configuration in config.json. Please check the file.")
        return

    # Construct the target URL
    target_url = f"https://analytics.google.com/analytics/web/?authuser=0#/a{account_id}p{property_id}/admin/property-users"

    async with async_playwright() as p:
        # Launch a persistent browser context with stealth options
        context = await p.chromium.launch_persistent_context(
            USER_DATA_DIR,
            headless=False,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--disable-dev-shm-usage',
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-web-security',
                '--disable-features=VizDisplayCompositor'
            ],
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        )
        # Use the first page if it exists, otherwise create a new one.
        page = context.pages[0] if context.pages else await context.new_page()
        
        # Remove automation indicators
        await page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined,
            });
        """)

        print(f"Navigating to user management page: {target_url}")
        await page.goto(target_url)

        # Check if we need to log in by looking for a unique element on the GA page
        # A robust check is to look for the account name or something that only appears when logged in.
        # For now, we'll check for the "Add" button as a proxy for being logged in.
        add_button_locator = page.get_by_role("button", name="Add", exact=True)

        try:
            await add_button_locator.wait_for(timeout=15000)
            print("✅ Successfully logged in and on the user management page.")
        except Exception:
            print("\n" + "="*50)
            print("ACTION REQUIRED: You are not logged in.")
            print("Please log in to your Google Account in the browser window.")
            print(f"Once you are logged in and can see the GA4 Admin page for property {property_id},")
            print("you can either close the browser and run the script again,")
            print("or just wait for this script to continue after you log in.")
            print("="*50 + "\n")
            # Wait longer for the user to manually log in
            await add_button_locator.wait_for(timeout=300000) # 5 minutes
            print("✅ Login detected. Proceeding with automation...")


        try:
            print("Looking for the 'Add users' button...")
            # Click the blue 'Add' button at the top right
            await add_button_locator.click()
            
            # Click 'Add users' from the dropdown menu
            # Using a more robust text-based locator
            await page.locator('button:has-text("Add users")').click()
            
            print("Filling in new user details...")
            # Enter the new user's email address
            await page.get_by_placeholder("Enter email addresses").fill(new_user_email)
            
            # Select the predefined role
            print(f"Selecting role: {new_user_role}")
            await page.get_by_role("radio", name=new_user_role, exact=True).click()
            
            # Click the final 'Add' button in the dialog
            # The button is inside a form, let's be more specific
            add_in_dialog_button = page.locator('//form[contains(., "Add users")]//button[contains(., "Add")]')
            await add_in_dialog_button.click()

            # --- Verification Step ---
            print("Verifying if the user was added successfully...")
            
            # Check if the new user's email is visible in the user list
            await expect(page.get_by_text(new_user_email, exact=True)).to_be_visible(timeout=15000)
            
            print(f"✅ Successfully added user: {new_user_email}")

        except Exception as e:
            print(f"❌ An error occurred during automation: {e}")
            # Check for 'already has access' message
            error_popup = page.get_by_text("already has access", re.IGNORECASE)
            if await error_popup.is_visible():
                print("Error detail: The user already has access to this property.")
            
            screenshot_path = "error_screenshot.png"
            await page.screenshot(path=screenshot_path)
            print(f"A screenshot has been saved as '{screenshot_path}'")

        finally:
            print("Automation finished. Closing browser.")
            await context.close()

async def main():
    # Before running, ensure Playwright browsers are installed.
    # In your terminal, run: playwright install
    await run_ga_automation()

if __name__ == "__main__":
    if sys.version_info[0] == 3 and sys.version_info[1] >= 8 and sys.platform.startswith('win'):
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main()) 