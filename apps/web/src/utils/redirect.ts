/**
 * Login redirect destinations.
 *
 * `?next=` is attacker-influenceable, so every destination is validated before
 * it is used. Lives outside the pages so both the login screens and the OAuth
 * callback can apply the same rule rather than re-implementing it.
 */

export const isSafeLoginDestination = (value: string): boolean => {
  if (!value || !value.startsWith("/") || value.startsWith("//")) return false;
  // eslint-disable-next-line no-control-regex
  if (/[\\\u0000-\u001f\u007f]/.test(value)) return false;
  try {
    const parsed = new URL(value, window.location.origin);
    if (
      parsed.origin !== window.location.origin ||
      !parsed.pathname.startsWith("/") ||
      parsed.pathname.startsWith("//")
    ) {
      return false;
    }
    const pathname = parsed.pathname.toLowerCase();
    const blocked = ["/login", "/register", "/sso-callback"];
    if (blocked.some((b) => pathname === b || pathname.startsWith(`${b}/`))) {
      return false;
    }
    return true;
  } catch {
    return false;
  }
};

export const getLoginDestination = (location: { search: string; state: unknown }): string => {
  const from = (location.state as { from?: string })?.from || "/dashboard";
  const requestedNext = new URLSearchParams(location.search).get("next");
  if (requestedNext && isSafeLoginDestination(requestedNext)) return requestedNext;
  return isSafeLoginDestination(from) ? from : "/dashboard";
};
