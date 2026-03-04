import discord
from datetime import datetime, timezone
import os
import requests
from async_tls_client import AsyncClient  # TLS spoofing library

# Custom HTTPClient with TLS/browser spoofing to bypass Cloudflare blocks
class CustomHTTP(discord.http.HTTPClient):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Spoof modern Chrome TLS fingerprint (update to latest supported, e.g., "chrome126" if available)
        self.tls_client = AsyncClient(
            client_identifier="chrome124",          # Try "chrome126" or check library for newest
            random_tls_extension_order=True,
            # Optional: Add residential proxy if still blocked (format: http://user:pass@ip:port)
            # proxy="http://your-proxy-here",
        )
        # Force a real browser User-Agent to match the spoof (helps consistency)
        self.user_agent_header = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"}

    async def request(self, route, *, files=None, form=None, **kwargs):
        method = route.method
        url = str(route)
        headers = kwargs.pop('headers', {})
        headers.update(self.user_agent_header)   # Consistent UA
        headers.update(self.token_header)        # Auth token
        params = kwargs.pop('params', None)
        data = kwargs.pop('data', None)
        json = kwargs.pop('json', None)
        if form:
            data = form  # Multipart support

        try:
            response = await self.tls_client.execute(
                method=method.lower(),
                url=url,
                headers=headers,
                params=params,
                data=data,
                json=json,
                files=files,                  # Better file handling
                follow_redirects=True
            )
        except Exception as e:
            print(f"TLS spoofed request failed: {e}")
            raise

        # Proper async-compatible response wrapper
        class DummyResponse:
            def __init__(self, resp):
                self.status = resp.status_code
                self.reason = resp.reason_phrase or ""
                self.headers = resp.headers
                self._resp = resp  # Keep original for async methods

            async def text(self):
                return await self._resp.text()   # Assume async; if sync, use asyncio.to_thread

            async def json(self):
                return await self._resp.json()

            async def read(self):
                return await self._resp.read()

        return DummyResponse(response)

# Setup the selfbot client
client = discord.Client(self_bot=True)
client.http = CustomHTTP()  # Use our spoofed HTTP client

webhook_url = os.getenv("WEBHOOK_URL")

def send_webhook_message(content):
    if not webhook_url:
        print("Webhook URL missing – set WEBHOOK_URL in Railway variables")
        return
    
    try:
        data = {"content": content}
        response = requests.post(webhook_url, json=data)
        if response.status_code != 204:
            print(f"Webhook send failed: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"Webhook error: {e}")

@client.event
async def on_ready():
    print(f'Logged in as {client.user} (ID: {client.user.id})')
    print('Selfbot is ready and connected!')

@client.event
async def on_member_join(member):
    try:
        guild = member.guild
        account_age = (datetime.now(timezone.utc) - member.created_at).days
        
        message = (
            f"📥 **New Join Detected**\n"
            f"Server: **{guild.name}**\n"
            f"User: {member.name} ({member})\n"
            f"User ID: {member.id}\n"
            f"Account Age: {account_age} days"
        )
        
        send_webhook_message(message)
        print(f"Webhook sent for join: {member.name}")
    except Exception as e:
        print(f"on_member_join error: {e}")

# Token check
user_token = os.environ.get("DISCORD_TOKEN")
if not user_token:
    print("DISCORD_TOKEN is missing! Set it in Railway Variables.")
    raise ValueError("DISCORD_TOKEN required")

print("Starting selfbot with TLS spoofing...")
client.run(user_token)