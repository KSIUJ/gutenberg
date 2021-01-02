import Cookies from 'js-cookie';

function getCsrfToken() {
  return Cookies.get('csrftoken');
}

// eslint-disable-next-line import/prefer-default-export
export { getCsrfToken };
