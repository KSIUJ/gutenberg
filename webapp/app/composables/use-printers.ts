export const usePrinters = () => {
  const { $auth } = useNuxtApp();
  const apiRepository = useApiRepository();

  const printers = useAsyncData('printers', apiRepository.getPrinters);

  // Refresh the printer list when the authenticated user changes
  watch(() => {
    if ($auth.me.value === Unauthenticated) return null;
    return $auth.me.value.username;
  }, (newUsername, previousUsername) => {
    // Do not automatically refresh the printer list if the user is not signed in.
    // This way existing forms will not become invalid when the session expires.
    if (newUsername === null) return;

    if (newUsername !== previousUsername) {
      printers.refresh().catch((error) => {
        console.warn('Got an error when refreshing printer list:', error);
      });
    }
  });

  return printers;
};
