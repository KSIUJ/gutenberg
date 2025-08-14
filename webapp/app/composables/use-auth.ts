export const useAuth = async () => {
  const me = await useAuthMe();
  const apiRepository = useApiRepository();

  const login = async (username: string, password: string) => {
    await apiRepository.refreshCsrfToken();
    await apiRepository.login(username, password);
    await me.refresh();
  };

  return {
    login,
  }
}
