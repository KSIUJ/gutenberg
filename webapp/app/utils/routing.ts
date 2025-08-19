import type {RouteLocationNormalized} from "#vue-router";

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
