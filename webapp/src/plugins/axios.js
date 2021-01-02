/*eslint-disable */
import Vue from 'vue';
import axios from 'axios';

// Full config:  https://github.com/axios/axios#request-config
// axios.defaults.baseURL = process.env.baseURL || process.env.apiUrl || '';
// axios.defaults.headers.common['Authorization'] = AUTH_TOKEN;
// axios.defaults.headers.post['Content-Type'] = 'application/x-www-form-urlencoded';

const config = {
  // baseURL: process.env.baseURL || process.env.apiUrl || ""
  timeout: 1500 * 1000, // Timeout
  withCredentials: true, // Check cross-site Access-Control
  xsrfCookieName: 'csrftoken',
  xsrfHeaderName: 'X-CSRFTOKEN',
};

const _axios = axios.create(config);

// _axios.interceptors.request.use(
//   (config) =>
//     // Do something before request is sent
//     config,
//   (error) =>
//     // Do something with request error
//     Promise.reject(error),
// );

// Add a response interceptor
_axios.interceptors.response.use(
  (response) =>
    // Do something with response data
    response,
  (error) => {
    if (error.response && error.response.status === 403) {
      window.location.reload(false);
      return Promise.reject(error);
    }
    alert(error + (error.response ? '\n' + JSON.stringify(error.response.data) : ''));
    window.location.reload(false);
    // Do something with response error
    return Promise.reject(error);
  },
);

Plugin.install = function (Vue, options) {
  Vue.axios = _axios;
  window.axios = _axios;
  Object.defineProperties(Vue.prototype, {
    axios: {
      get() {
        return _axios;
      },
    },
    $axios: {
      get() {
        return _axios;
      },
    },
  });
};

Vue.use(Plugin);

export default Plugin;
