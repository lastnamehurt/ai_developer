# GitLab MCP Authentication Issue - Investigation Report

## Problem Statement

When attempting to use the GitLab MCP tools to fetch merge request discussions from `https://gitlab.checkrhq.net/platform/checkr/-/merge_requests/36089`, Claude Code returned:

```
MCP error -32603: GitLab API error: 401 Unauthorized
{"message":"401 Unauthorized"}
```

## Investigation Process

### 1. Environment Variable Setup ✓
First, I verified that the necessary GitLab credentials were available:

```bash
$ echo $GITLAB_PERSONAL_ACCESS_TOKEN
yBvdEs5nGM_aCj4u-wpa

$ echo $GITLAB_URL
http://gitlab.checkrhq.net
```

Both variables were present in the environment.

### 2. MCP Configuration Review ✓
I examined the GitLab MCP configuration at `src/aidev/configs/mcp-servers/gitlab.json`:

```json
{
  "name": "gitlab",
  "description": "GitLab API integration (issues, MRs, CI/CD, wikis)",
  "type": "stdio",
  "command": "npx",
  "args": ["-y", "@zereight/mcp-gitlab"],
  "env": {
    "GITLAB_PERSONAL_ACCESS_TOKEN": "${GITLAB_PERSONAL_ACCESS_TOKEN}",
    "GITLAB_API_URL": "${GITLAB_API_URL:-https://gitlab.checkrhq.net/api/v4}",
    "GITLAB_READ_ONLY_MODE": "false",
    "USE_GITLAB_WIKI": "${USE_GITLAB_WIKI:-true}",
    "USE_MILESTONE": "${USE_MILESTONE:-true}",
    "USE_PIPELINE": "${USE_PIPELINE:-true}"
  }
}
```

Configuration looks correct - it should expand `GITLAB_PERSONAL_ACCESS_TOKEN` from the environment.

### 3. API Endpoint Testing
I tested the GitLab API directly with the credentials to verify token validity:

```bash
# First attempt - with HTTP (what GITLAB_URL was set to)
curl -H "PRIVATE-TOKEN: yBvdEs5nGM_aCj4u-wpa" \
  http://gitlab.checkrhq.net/api/v4/user
# Result: 308 Permanent Redirect (HTTP to HTTPS)

# Second attempt - with HTTPS
curl -H "PRIVATE-TOKEN: yBvdEs5nGM_aCj4u-wpa" \
  https://gitlab.checkrhq.net/api/v4/user
# Result: ✓ 200 OK (User details returned)
```

**Finding**: The token is **valid** and works with HTTPS.

### 4. Successful API Call
Using the API directly with HTTPS returned full user data:
```json
{
  "id": 711,
  "username": "courtney.hurt",
  "name": "Courtney Hurt",
  "state": "active",
  ...
}
```

## Root Cause Analysis

The GitLab MCP is failing due to **one or more of the following**:

### A. Environment Variable Expansion Issue (Most Likely)
The `@zereight/mcp-gitlab` server is spawned as a subprocess by Claude Code's MCP runner. While the configuration file specifies environment variable expansion (e.g., `${GITLAB_PERSONAL_ACCESS_TOKEN}`), there are several potential failure points:

1. **MCP Server Initialization Timing**: The MCP server may have been initialized before the `ai env set` commands were executed, meaning it doesn't have access to the encrypted variables stored in `~/.aidev/.env`

2. **Variable Expansion Scope**: The MCP config generator may not be properly merging and expanding:
   - Global environment variables from `~/.aidev/.env`
   - Project environment variables from `.aidev/.env`
   - System environment variables

3. **Missing `GITLAB_API_URL`**: The config has a default of `https://gitlab.checkrhq.net/api/v4`, but the `GITLAB_URL` environment variable was set to `http://gitlab.checkrhq.net`. The MCP server might:
   - Not be reading the default correctly
   - Be trying to use the HTTP URL instead of HTTPS
   - Not have the correct API URL format

### B. HTTP vs HTTPS Issue
The GitLab instance redirects HTTP to HTTPS with a 308 Permanent Redirect. The MCP server might:
- Not follow redirects automatically
- Have SSL/TLS certificate validation issues
- Be using an incompatible HTTP client library

### C. Token Encryption/Storage
The token was stored encrypted via `ai env set --encrypt`, but:
- Claude Code's MCP runtime may not be decrypting it properly
- The MCP config generator may not have access to the encryption key
- The MCP server subprocess may not inherit the decrypted variables

## What Was Done

### Immediate Actions Taken
1. Set environment variables using aidev CLI (encrypted):
   ```bash
   ai env set GITLAB_PERSONAL_ACCESS_TOKEN "yBvdEs5nGM_aCj4u-wpa" --encrypt
   ai env set GITLAB_URL "https://gitlab.checkrhq.net"
   ai env set GITLAB_API_URL "https://gitlab.checkrhq.net/api/v4"
   ```

2. Verified token validity with direct API call
3. **Workaround**: Used direct curl API calls to fetch MR discussions

### What Didn't Work
- Simply setting environment variables didn't fix the MCP authentication
- The MCP server continued to return 401 errors even after configuration

## Why the Workaround Succeeded

Calling the GitLab API directly with curl succeeded because:
1. ✓ The token is valid
2. ✓ The API endpoint is correct (`https://gitlab.checkrhq.net/api/v4`)
3. ✓ The direct HTTP request doesn't rely on MCP server subprocess environment variable inheritance
4. ✓ HTTPS is properly used

## Recommendations for Long-term Fix

### 1. **Verify MCP Server Configuration at Runtime**
Add logging to the MCP config generator to show:
- What environment variables are being passed to the MCP subprocess
- The expanded GITLAB_API_URL value
- Whether variables are decrypted before passing to subprocess

### 2. **Update MCP Config to Use HTTPS Explicitly**
Modify `gitlab.json` to ensure HTTPS is always used:
```json
{
  "env": {
    "GITLAB_PERSONAL_ACCESS_TOKEN": "${GITLAB_PERSONAL_ACCESS_TOKEN}",
    "GITLAB_API_URL": "${GITLAB_API_URL:-https://gitlab.checkrhq.net/api/v4}",
    ...
  }
}
```

### 3. **Add Environment Variable Validation**
In `src/aidev/errors.py` or a new preflight check, verify:
- `GITLAB_PERSONAL_ACCESS_TOKEN` is set before launching any GitLab tools
- `GITLAB_API_URL` uses HTTPS protocol
- Add a test endpoint call to validate token before handing off to MCP

### 4. **Test MCP Initialization in CI/CD**
Add integration tests that:
- Initialize the MCP server with test credentials
- Verify it can authenticate with the GitLab API
- Catch auth failures early

### 5. **Document MCP Setup Process**
Create a guide for users on:
- How to properly configure GitLab credentials with aidev
- Why HTTPS is required
- How to troubleshoot 401 errors
- Alternative direct API approaches if MCP fails

## Conclusion

The GitLab MCP authentication issue is likely caused by **environment variable expansion not working properly when the MCP subprocess is spawned**. The credentials are valid (verified via direct API call), but they're not being passed correctly to the `@zereight/mcp-gitlab` server running as a subprocess.

The immediate workaround of using direct API calls works perfectly and can serve as a fallback mechanism if MCP issues persist.
