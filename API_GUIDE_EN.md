# How to get API ID and API Hash — Full guide

If you see "object Object" or any weird popup when trying to use my.telegram.org, follow this guide.

---

## Fix "object Object" error first

This usually happens because of browser or extensions.

**Try this:**

1. **Use another browser** — Chrome, Firefox, or Edge. Don't use Opera or old browsers.
2. **Turn off ad blockers** — They can break the site.
3. **Disable VPN** — Some VPNs cause issues.
4. **Incognito/Private mode** — Open my.telegram.org in a private window.
5. **Clear cache** — Settings → Clear browsing data → Cached images and files.

---

## Step-by-step: Get API ID and API Hash

### 1. Open the site

Go to: **https://my.telegram.org**

### 2. Log in

- Enter your **phone number** with country code (e.g. +1234567890)
- Click **Next**
- You'll get a **code** in Telegram — enter it
- If you have 2FA — enter your cloud password

### 3. Create an app

- After login, click **API development tools**
- Fill the form:
  - **App title:** Psylocyba Tools (or anything)
  - **Short name:** psytools (or anything, latin only)
  - **URL:** leave empty or put https://t.me
  - **Platform:** Desktop
  - **Description:** leave empty
- Click **Create application**

### 4. Copy your credentials

You'll see:

- **App api_id:** a number (e.g. 12345678)
- **App api_hash:** a long string of letters and numbers

Copy both and paste them into Psylocyba Tools in the API settings.

---

## If it still doesn't work

**"object Object" keeps showing:**

- Try on your **phone** — open my.telegram.org in mobile browser (Chrome, Safari)
- Log in there, create the app, copy api_id and api_hash
- Send them to your PC and paste into the program

**Can't receive the code:**

- Make sure you use the **correct phone number** (with + and country code)
- Check that Telegram is installed and you're logged in
- Wait a few minutes and try again

**Site doesn't load:**

- Check your internet
- Try without VPN
- Try from another device or network
