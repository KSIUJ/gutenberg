export const useApiRepository = () => {
  const { $api } = useNuxtApp();
  return createApiRepository($api);
};
