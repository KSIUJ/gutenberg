const API = {
  me: '/api/me/?format=json',
  logout: '/oidc/logout/',
  ipp: '/ipp/',
  resetToken: '/api/resettoken/',
  jobs: '/api/jobs/',
  cancelJob: '/cancel',
  submit: '/api/jobs/submit/?format=json',
};

// eslint-disable-next-line import/prefer-default-export
export { API };
