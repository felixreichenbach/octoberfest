import { getWebInstrumentations, initializeFaro } from '@grafana/faro-web-sdk'
import { TracingInstrumentation } from '@grafana/faro-web-tracing'

// Grafana Faro (Frontend Observability). Enabled only when VITE_FARO_URL is set
// at build time (the app's collector URL from Grafana Cloud); otherwise a no-op.
const url = import.meta.env.VITE_FARO_URL

export const faro = url
  ? initializeFaro({
      url,
      app: {
        // Must match the app name in Grafana Cloud Frontend Observability.
        name: import.meta.env.VITE_FARO_APP_NAME || 'Oktoberfest',
        version: import.meta.env.VITE_APP_VERSION || '1.0.0',
        environment: import.meta.env.VITE_FARO_ENVIRONMENT || 'production',
      },
      // Harmless browser noise that isn't a real application error.
      ignoreErrors: [
        /^ResizeObserver loop limit exceeded$/,
        /^ResizeObserver loop completed with undelivered notifications$/,
        /^Script error\.$/,
        /chrome-extension:\/\//,
        /moz-extension:\/\//,
      ],
      instrumentations: [
        ...getWebInstrumentations({ captureConsole: true }),
        // Propagates W3C trace context on /api calls so browser spans link to backend traces.
        new TracingInstrumentation({
          instrumentationOptions: {
            propagateTraceHeaderCorsUrls: [/\/api\//, new RegExp(`${window.location.origin}/api`)],
          },
        }),
      ],
    })
  : null
