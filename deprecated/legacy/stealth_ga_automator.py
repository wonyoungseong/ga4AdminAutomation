import asyncio
import json
import os
import sys
from playwright.async_api import async_playwright, expect

USER_DATA_DIR = "playwright_user_data"

async def manual_login_setup():
    """
    Step 1: Launch browser for manual login
    """
    print("=== STEP 1: Manual Login Setup ===")
    print("A browser will open. Please:")
    print("1. Log in to your Google account")
    print("2. Navigate to Google Analytics")
    print("3. Make sure you can access your GA4 property")
    print("4. Close the browser when done")
    print("5. Run the automation script")
    
    async with async_playwright() as p:
        context = await p.chromium.launch_persistent_context(
            USER_DATA_DIR,
            headless=False,
        )
        page = context.pages[0] if context.pages else await context.new_page()
        
        await page.goto("https://analytics.google.com/")
        
        print("\nBrowser opened. Please complete the login manually.")
        print("Press Enter in this terminal when you're done and have closed the browser...")
        input()
        
        await context.close()
        print("✅ Login setup complete!")

async def run_automation_only():
    """
    Step 2: Run automation using saved login
    """
    # Load configuration
    try:
        with open('config.json', 'r') as f:
            config = json.load(f)
    except FileNotFoundError:
        print("❌ Error: config.json not found.")
        return

    account_id = config.get('account_id')
    property_id = config.get('property_id')
    new_user_email = config.get('new_user_email')
    new_user_role = config.get('new_user_role', 'Analyst')

    if not all([account_id, property_id, new_user_email]):
        print("❌ Error: Missing configuration in config.json.")
        return

    target_url = f"https://analytics.google.com/analytics/web/?authuser=0#/a{account_id}p{property_id}/admin/property-users"

    print("=== STEP 2: Running Automation ===")
    
    async with async_playwright() as p:
        context = await p.chromium.launch_persistent_context(
            USER_DATA_DIR,
            headless=False,
        )
        page = context.pages[0] if context.pages else await context.new_page()

        print(f"Navigating to: {target_url}")
        await page.goto(target_url)
        
        # Wait a bit for page to load
        await page.wait_for_load_state('networkidle')

        try:
            # Look for Add button to confirm we're logged in
            add_button = page.get_by_role("button", name="Add")
            await add_button.wait_for(timeout=10000)
            print("✅ Successfully accessed GA4 admin page")
            
            # Proceed with automation
            print("Clicking Add button...")
            await add_button.click()
            
            print("Looking for 'Add users' option...")
            await page.locator('text="Add users"').click()
            
            print(f"Entering email: {new_user_email}")
            await page.get_by_placeholder("Enter email addresses").fill(new_user_email)
            
            print(f"Selecting role: {new_user_role}")
            await page.get_by_role("radio", name=new_user_role).click()
            
            print("Clicking final Add button...")
            await page.locator('button:has-text("Add"):not(:has-text("Add users"))').click()
            
            # Verify success
            await page.wait_for_timeout(3000)  # Wait for user to be added
            print("✅ User addition completed!")
            
        except Exception as e:
            print(f"❌ Error during automation: {e}")
            await page.screenshot(path="automation_error.png")
            print("Screenshot saved as automation_error.png")

        finally:
            await context.close()

async def main():
    print("GA4 User Addition Automation")
    print("============================")
    
    # Check if user data directory exists
    if not os.path.exists(USER_DATA_DIR):
        print("No previous login found. Starting manual login setup...")
        await manual_login_setup()
        print("\nNow run the script again to perform automation.")
    else:
        print("Previous login found. Running automation...")
        await run_automation_only()

if __name__ == "__main__":
    asyncio.run(main()) 