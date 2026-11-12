# APIMatic workflow

`docs/api/openapi.yaml` is the API contract source for APIMatic. Export and
check it before importing:

```powershell
make openapi-export
make openapi-check
```

The APIMatic CLI's documented quickstart creates a local API Documentation
Portal from an imported API definition. Generate all output under the ignored
`build/apimatic/` directory, not under `apps/` or `packages/`.

## Import the contract and generate the portal and SDKs

The APIMatic [CLI Quickstart](https://docs.apimatic.io/cli-getting-started/portal-quickstart-dac/)
documents the following setup. Node.js 20 or newer and npm are required.

1. Install the CLI:

   ```powershell
   npm install -g @apimatic/cli@1
   ```

2. Sign in to your APIMatic account. The CLI opens a browser for account
   authentication; this flow does not use `APIMATIC_AUTH_KEY`.

   ```powershell
   apimatic auth login
   apimatic auth status
   ```

3. From the repository root, create the ignored output directory and start the
   interactive quickstart there:

   ```powershell
   New-Item -ItemType Directory -Force build\apimatic | Out-Null
   Set-Location build\apimatic
   apimatic quickstart
   ```

4. In the wizard, choose **API Documentation Portal**, import the local
   `docs/api/openapi.yaml` file (from this working directory:
   `..\..\docs\api\openapi.yaml`), and select both **TypeScript** and **Python**
   when asked which SDKs to generate.
5. Keep the generated portal and SDK artifacts inside `build/apimatic/`. The
   CLI reports the artifact location and starts a local preview; use
   `apimatic portal serve` from the generated project directory to preview it
   later.
6. Publish the generated portal by deploying its reported static-artifact
   folder to your static host. APIMatic documents the
   [hosting flow](https://docs.apimatic.io/docs-as-code/hosting-your-generated-portal/);
   its hosted-portal option requires contacting APIMatic support.

The APIMatic
[SDK generation overview](https://docs.apimatic.io/generate-sdks/overview-sdks/)
lists TypeScript and Python as supported SDK languages. The CLI's
[SDK-generation reference](https://docs.apimatic.io/generate-sdks/create-sdks/create-sdks-through-cli/)
documents standalone SDK generation as well; the portal wizard above keeps
this workflow aligned with the imported contract and output-directory rule.

## Auth key handling

APIMatic calls its API credential an **Auth Key**. Its
[official instructions](https://docs.apimatic.io/account-management/obtaining-auth-keys/)
describe creating the key in **Settings → Account Settings → API
Authentication** and sending it in an Authorization header when calling
APIMatic APIs. Do not put a real key in this repository, command-line
arguments, documentation, examples, or generated output.

For any future direct APIMatic API integration, make the key available only in
the current process environment variable `APIMATIC_AUTH_KEY`. For example,
prompt for it without echoing or placing the value in shell history:

```powershell
$authKey = Read-Host "APIMatic Auth Key" -AsSecureString
$env:APIMATIC_AUTH_KEY = [System.Net.NetworkCredential]::new("", $authKey).Password
Remove-Variable authKey
```

The `.env.example` entry is intentionally empty as a name-only reminder; never
fill it with the key. The current CLI workflow uses `apimatic auth login` and
does not read `APIMATIC_AUTH_KEY`. APIMatic is used only for documentation and
SDK generation, never as an application runtime data source.

## Contract notes

- Regenerate the spec with `make openapi-export` after route/schema changes and
  run `make openapi-check` before importing it.
- The current API has no price-comparison route yet, so no price-comparison
  operation or example is added to the contract.
- Generated files under `build/apimatic/` are local artifacts; do not commit
  them or copy them into the web app or API client package.
