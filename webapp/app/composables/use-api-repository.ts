export const useApiRepository = () => {
  const { $api } = useNuxtApp();
  return apiRepository($api);
}
