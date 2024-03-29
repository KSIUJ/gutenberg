/*eslint-disable */
import Vue from 'vue';
import axios from 'axios';

const config = {
  // baseURL: process.env.baseURL || process.env.apiUrl || ""
  timeout: 5 * 60 * 1000, // Timeout
  withCredentials: true, // Check cross-site Access-Control
  xsrfCookieName: 'csrftoken',
  xsrfHeaderName: 'X-CSRFTOKEN',
};

const _axios = axios.create(config);

// Add a response interceptor
_axios.interceptors.response.use(
  (response) =>
    // Do something with response data
    response,
  (error) => {
    if (error.config.noIntercept) {
      return Promise.reject(error);
    }
    if (error.response && error.response.status === 403) {
      window.location.reload(false);
      return Promise.reject(error);
    }
    if (error.response && error.response.status === 404) {
      alert(error);
      return Promise.reject(error);
    }
    if (error.response) {
      console.log(JSON.stringify(error.response.data));
    }
    alert(error);
    window.location.reload(false);
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
