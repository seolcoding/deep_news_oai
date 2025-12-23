# Deploy — Deploy your app

- Source: https://developers.openai.com/apps-sdk/deploy
- Captured: 2025-12-22

## Extracted text

Deployment options

Once you have a working MCP server and component bundle, host them behind a stable HTTPS endpoint. Deployment platforms that work well with Apps SDK include:

Managed containers – Fly.io, Render, or Railway for quick spin-up and automatic TLS.
Cloud serverless – Google Cloud Run or Azure Container Apps if you need scale-to-zero, keeping in mind that long cold starts can interrupt streaming HTTP.
Kubernetes – for teams that already run clusters. Front your pods with an ingress controller that supports server-sent events.

Regardless of platform, make sure /mcp stays responsive, supports streaming responses, and returns appropriate HTTP status codes for errors.

Local development

During development you can expose your local server to ChatGPT using a tunnel such as ngrok:

ngrok http 2091
# https://<subdomain>.ngrok.app/mcp → http://127.0.0.1:2091/mcp

Keep the tunnel running while you iterate on your connector. When you change code:

Rebuild the component bundle (npm run build).
Restart your MCP server.
Refresh the connector in ChatGPT settings to pull the latest metadata.

Environment configuration
- Secrets – store API keys or OAuth client secrets outside your repo. Use platform-specific secret managers and inject them as environment variables.
- Logging – log tool-call IDs, request latency, and error payloads. This helps debug user reports once the connector is live.
- Observability – monitor CPU, memory, and request counts so you can right-size your deployment.

Dogfood and rollout

Before launching broadly:

Gate access – keep your connector behind developer mode or a Statsig experiment flag until you are confident in stability.
Run golden prompts – exercise the discovery prompts you drafted during planning and note precision/recall changes with each release.
Capture artifacts – record screenshots or screen captures showing the component in MCP Inspector and ChatGPT for reference.

When you are ready for production, update directory metadata, confirm auth and storage are configured correctly, and publish change notes in Release Notes.

Next steps
- Connect your deployed endpoint to ChatGPT using the steps in Connect from ChatGPT.
- Validate tooling and telemetry with the Test your integration guide.
- Keep a troubleshooting playbook handy via Troubleshooting so on-call responders can quickly diagnose issues.
