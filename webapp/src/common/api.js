const API = {
  me: '/api/me/?format=json',
  logout: '/oidc/logout/',
  ipp: '/ipp/',
  resetToken: '/api/resettoken/',
  jobs: '/api/jobs/',
  cancelJob: '/cancel',
  runJob: '/run_job',
  upload: '/upload_artefact',
  submit: '/api/jobs/submit/?format=json',
  create: '/api/jobs/create_job/?format=json',
  printers: '/api/printers/?format=json',
};

// eslint-disable-next-line import/prefer-default-export
export { API };
