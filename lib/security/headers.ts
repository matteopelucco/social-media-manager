export function securityHeaders(input: { isDev: boolean; nonce: string }): Record<string, string> {
  const { isDev, nonce } = input;
  const scriptSrc = `script-src 'self' 'nonce-${nonce}' 'strict-dynamic'${isDev ? " 'unsafe-eval'" : ""}`;
  const csp = [
    "default-src 'self'",
    scriptSrc,
    "style-src 'self' 'unsafe-inline'",
    "img-src 'self' blob: data:",
    "font-src 'self'",
    "object-src 'none'",
    "base-uri 'self'",
    "form-action 'self'",
    "frame-ancestors 'none'",
  ].join("; ");
  return {
    "Cache-Control": "no-store",
    "Content-Security-Policy": csp,
    "X-Frame-Options": "DENY",
  };
}
