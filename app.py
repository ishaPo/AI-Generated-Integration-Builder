import json
import os
import re
import streamlit as st
import requests
from bs4 import BeautifulSoup
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

SYSTEM_PROMPT = """You are an expert integration engineer with deep knowledge of REST APIs. You will receive API documentation for {integration_name}.

CRITICAL RULE: Every endpoint path, parameter name, header, and field you reference MUST appear verbatim in the documentation provided. If a capability is not documented, do NOT invent it — skip it and note "Not documented in provided docs" as a code comment.

NEVER use hedging phrases like "let's assume", "typically", "we'd simulate", "a more robust solution would", "we'll manually increment". If the docs don't specify, write a comment: "# [aspect] not specified in provided docs".

Generate 6 components, each as a Python code string:

1. api_client: A Python class wrapping HTTP calls. Use the EXACT base URL from docs. Use the EXACT auth header format from docs (e.g., 'Authorization: Bearer <token>' if that's what docs say).

2. auth: Complete authentication setup. Identify the auth scheme(s) from docs:
   - If OAuth2: show authorization URL, token exchange, refresh flow with EXACT URLs from docs
   - If API key / PAT: show how to obtain it (link from docs), env var storage, attachment to requests
   - List required scopes/permissions for user and usage endpoints
   - DO NOT just write api_key = "YOUR_KEY" — show the actual flow with comments referencing the docs

3. data_retrieval: Functions to fetch users and usage data. For each function:
   - Use the EXACT endpoint path from docs (e.g., '/scheduled_events' not '/events')
   - Include required and optional query parameters as documented
   - Include type hints and return parsed JSON

4. error_handling: Map this API's specific error codes from docs to actionable handling. Include rate limit (429) handling with backoff using the actual retry-after header name documented.

5. pagination: Identify the EXACT pagination scheme from docs (cursor / offset / page / link-header / continuation token). Show working code with the exact parameter names documented. If the API uses different schemes per endpoint, show both. If you cannot find pagination details in docs, write that as a comment and provide a generic template.

6. logging: Structured logging with request_id correlation, redaction of credentials and PII fields (email, phone, tokens), and log levels matching severity.

Return ONLY valid JSON with keys: api_client, auth, data_retrieval, error_handling, pagination, logging. Each value is a Python code string."""

TABS = ["api_client", "auth", "data_retrieval", "error_handling", "pagination", "logging"]
TAB_LABELS = ["API Client", "Auth", "Data Retrieval", "Error Handling", "Pagination", "Logging"]


def fetch_page_text(url: str) -> str:
    resp = requests.get(url, timeout=15)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    return soup.get_text(separator="\n", strip=True)


def generate_integration(integration_name: str, docs_text: str) -> str:
    system = SYSTEM_PROMPT.format(integration_name=integration_name)
    user_prompt = f"Here is the API documentation for {integration_name}:\n\n{docs_text}"
    model = genai.GenerativeModel(
        "gemini-2.5-flash-lite",
        system_instruction=system,
        generation_config={"response_mime_type": "application/json", "max_output_tokens": 8000},
    )
    response = model.generate_content(user_prompt)
    return response.text


st.set_page_config(page_title="CloudEagle Integration Builder", layout="wide")

st.title("CloudEagle Integration Builder")
st.markdown("*From API docs to a working integration in 60 seconds. Built for CloudEagle.*")

st.markdown("**Quick-start:**")
qs_col1, qs_col2, qs_col3 = st.columns(3)
with qs_col1:
    if st.button("Try Calendly"):
        st.session_state["integration_name"] = "Calendly"
        st.session_state["api_docs_url"] = "https://developer.calendly.com/api-docs"
with qs_col2:
    if st.button("Try Slack"):
        st.session_state["integration_name"] = "Slack"
        st.session_state["api_docs_url"] = "https://api.slack.com/methods/auth.test"
with qs_col3:
    if st.button("Try GitHub"):
        st.session_state["integration_name"] = "GitHub"
        st.session_state["api_docs_url"] = "https://docs.github.com/en/rest/users/users"

col1, col2 = st.columns(2)
with col1:
    integration_name = st.text_input("Integration name", placeholder="e.g. Calendly", key="integration_name")
with col2:
    api_docs_url = st.text_input("API docs URL", placeholder="https://developer.example.com/docs", key="api_docs_url")

pasted_docs = st.text_area(
    "Or paste docs text directly (recommended for JS-heavy docs sites)",
    height=180,
    placeholder="Paste raw API documentation text here...",
)

st.text_input("API Token (for live sandbox test)", type="password", key="api_token",
              placeholder="Paste your bearer token here")
st.caption("Optional. Only needed for the Live Sandbox Test.")

if st.button("Generate Integration", type="primary"):
    if not integration_name.strip():
        st.error("Please enter an integration name.")
    elif not pasted_docs.strip() and not api_docs_url.strip():
        st.error("Please enter an API docs URL or paste docs text.")
    else:
        with st.spinner("Generating integration..."):
            if pasted_docs.strip():
                docs_text = pasted_docs.strip()
            else:
                try:
                    docs_text = fetch_page_text(api_docs_url.strip())
                except Exception as e:
                    st.error(f"Failed to fetch URL: {e}")
                    st.stop()

            docs_text = docs_text[:50_000]
            st.caption(f"Sending {len(docs_text):,} characters of docs to the model.")

            try:
                raw = generate_integration(integration_name.strip(), docs_text)
            except Exception as e:
                st.error(f"Gemini API error: {e}")
                st.stop()

            try:
                cleaned = raw.strip()
                if cleaned.startswith("```"):
                    cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
                    cleaned = re.sub(r"\s*```$", "", cleaned)
                cleaned = re.sub(r",(\s*[}\]])", r"\1", cleaned)
                try:
                    components = json.loads(cleaned)
                except json.JSONDecodeError:
                    from json_repair import repair_json
                    components = json.loads(repair_json(raw))
            except Exception as e:
                st.error(f"JSON parse error: {e}")
                st.text_area("Raw model response (for debugging)", raw, height=300)
                st.stop()

        st.session_state["components"] = components
        st.session_state["last_integration"] = integration_name.strip()

if "components" in st.session_state:
    components = st.session_state["components"]
    last_integration = st.session_state["last_integration"]

    st.success(f"Integration for **{last_integration}** generated successfully.")
    tabs = st.tabs(TAB_LABELS)
    for tab, key in zip(tabs, TABS):
        with tab:
            code = components.get(key, "# No code generated for this component.")
            st.code(code, language="python")

    st.divider()
    st.subheader("🚀 Live Sandbox Test")
    st.markdown("Click to call the API directly using the auth pattern the generated code uses.")

    LIVE_ENDPOINTS = {
        "calendly": ("GET", "https://api.calendly.com/users/me",
                     {"Authorization": "Bearer {token}"}),
        "slack": ("GET", "https://slack.com/api/auth.test",
                  {"Authorization": "Bearer {token}"}),
        "github": ("GET", "https://api.github.com/user",
                   {"Authorization": "Bearer {token}", "Accept": "application/vnd.github+json"}),
    }

    if st.button("Test against live API"):
        token = st.session_state.get("api_token", "").strip()
        key = last_integration.lower()
        if key not in LIVE_ENDPOINTS:
            st.info("Live test not configured for this integration yet")
        elif not token:
            st.error("Please enter an API token above before running the live test.")
        else:
            method, url, headers_template = LIVE_ENDPOINTS[key]
            headers = {k: v.format(token=token) for k, v in headers_template.items()}
            with st.spinner("Calling live API..."):
                try:
                    resp = requests.request(method, url, headers=headers, timeout=10)
                    if resp.status_code == 200:
                        st.success("✅ Live API call succeeded")
                        with st.expander("Response JSON"):
                            st.json(resp.json())
                        st.info(
                            "💡 In production, CloudEagle's runtime would execute the full generated manifest "
                            "in a sandboxed environment with rate limiting, dry-run mode, and audit logs."
                        )
                    else:
                        st.error(f"❌ {resp.status_code}: {resp.text[:500]}")
                except Exception as e:
                    st.error(f"❌ {e}")

    st.caption(
        "Calling the same endpoint and auth scheme used in the generated code. "
        "In production, CloudEagle's runtime would execute the full generated manifest "
        "in a sandboxed environment."
    )

st.divider()
st.caption("Prototype by Isha Syed | Model: Gemini 2.0 Flash | Built for CloudEagle PM assignment")
