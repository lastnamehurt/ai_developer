
## Current Verification Sprint: RESULTS

This section documents the results of the verification sprint for GitLab, AWS/S3, and Web search.

- **GitLab**:
  - **Result**: **Partial Success**. The NPM package `@zereight/mcp-gitlab` is active and valid. However, no public GitHub repository could be found.
  - **Recommendation**: Update the `install.command` to `npm install -g @zereight/mcp-gitlab` and remove the broken `repository` URL.

- **AWS / S3**:
  - **Result**: **Success (for S3)**. While no general-purpose "AWS" server was found, a promising, officially supported S3 server was located.
  - **Candidate Repository**: `https://github.com/aws-samples/sample-mcp-server-s3`
  - **Recommendation**: Update the existing **`s3`** entry (not the `aws` entry) to use this new repository. The exact `install.command` needs to be determined from the repository's README. The `aws` entry remains broken.

- **Web search**:
  - **Result**: **Success**. A promising, officially supported web search server backed by SerpApi was found.
  - **Candidate Repository**: `https://github.com/serpapi/mcp-serpapi`
  - **Recommendation**: Update the `web-search` entry to use this new repository. The `install.command` and required API keys need to be determined from the repository's README.


### Definitive Recommendations from Verification Sprint

- **GitLab**:
  - **Action**: Update entry.
  - **`repository`**: Remove this field as no public repo was found.
  - **`install.command`**: Set to `npm install -g @zereight/mcp-gitlab`.

- **S3**:
  - **Action**: Update the **`s3`** entry. The `aws` entry remains unfixed.
  - **`repository`**: Set to `https://github.com/aws-samples/sample-mcp-server-s3`.
  - **`install.type`**: Set to `manual`.
  - **`install.command`**: Set to a multi-step command: `git clone https://github.com/aws-samples/sample-mcp-server-s3 ~/.aidev/mcp-servers/s3 && cd ~/.aidev/mcp-servers/s3 && npm install`.
  - **`configuration.required`**: Add `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY`.

- **Web search**:
  - **Action**: Update entry.
  - **`repository`**: Set to `https://github.com/serpapi/mcp-serpapi`.
  - **`install.type`**: Set to `remote`.
  - **`install.command`**: Set to `npx -y mcp-remote https://mcp.serpapi.com`.
  - **`configuration.required`**: Add `SERPAPI_API_KEY` (as the remote URL will likely require it for auth).

