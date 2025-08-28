import type { LocationQueryValue, RouteLocationNormalized } from '#vue-router';

/**
 * Tries to resolve the `next` route using Vue Router.
 * If it succeeded and the route is an internal route (handled by Vue Router),
 * it returns that resolved route, otherwise returns `null`.
 */
const tryResolveInternalRoute = (next: string, current: RouteLocationNormalized) => {
  const router = useRouter();
  try {
    const resolvedNext = router.resolve(next, current);
    if (resolvedNext.matched.length > 0) return resolvedNext;
  } catch (error) {
    console.warn(`Resolving route ${next} failed`, error);
  }
  return null;
};

export const navigateToMaybeExternal = (next: string, current: RouteLocationNormalized) => {
  const internalRoute = tryResolveInternalRoute(next, current);
  if (internalRoute) return navigateTo(internalRoute);
  return navigateTo(next, {
    external: true,
  });
};

/**
 * @returns a single non-empty string parameter from the query value or `null` if there are
 * none or more than one such values.
 */
export const getSingleQueryParam = (
  value: undefined | LocationQueryValue | LocationQueryValue[],
): string | undefined => {
  if (value === undefined) return undefined;
  if (!Array.isArray(value)) return getSingleQueryParam([value]);
  const candidates = value.filter(x => typeof x === 'string' && x !== '');
  if (candidates.length === 1 && candidates[0] !== null) return candidates[0];
  return undefined;
};

/**
 * Returns the value of the `next` query parameter normalized as a relative path.
 * If the path is not a valid relative path returns `undefined`.
 *
 * SECURITY: The next parameter can only be used for same-origin redirects to avoid attacks with
 *           fabricated login URLs redirecting to other hosts.
 */
export const getNextQueryParam = (
  route: RouteLocationNormalized,
) => {
  const next = getSingleQueryParam(route.query.next);
  if (next === undefined) return undefined;

  let url: URL;
  try {
    url = new URL(next, window.location.origin);
  } catch (error) {
    console.warn(`Failed to parse next search query parameter: ${next}`, error);
    return undefined;
  }

  if (url.origin !== window.location.origin) {
    console.warn(`Invalid non-relative next search query parameter: ${next}`);
    return undefined;
  }

  return url.pathname + url.search + url.hash;
};

/**
 * Tries to parse a route query value to check if a boolean flag is set.
 * @returns `true` if the value contains at least one argument of the form:
 * `?x`, `?x=`, `?x=true` (any case), `?x=t` (any case) and `?x=1`
 * and `false` otherwise.
 *
 * @see https://router.vuejs.org/api/type-aliases/LocationQueryValue.html
 */
export const isQueryFlagEnabled = (
  value: undefined | LocationQueryValue | LocationQueryValue[],
): boolean => {
  if (value === undefined) return false;
  if (value === null) return true;
  if (typeof value === 'string') {
    return ['', 't', 'true', '1'].includes(value.toLowerCase());
  }
  return value.some(isQueryFlagEnabled);
};
