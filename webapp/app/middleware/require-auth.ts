export default defineNuxtRouteMiddleware(() => {
  const { $auth } = useNuxtApp();
  if ($auth.me.value !== Unauthenticated) return;
  return navigateTo(
    {
      path: '/login/',
      query: { next: useRoute().fullPath },
    },
    { external: true },
  );
});
