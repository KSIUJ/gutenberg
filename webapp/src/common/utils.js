import Cookies from "js-cookie";

function getCsrfToken() {
  return Cookies.get('csrftoken');
}

export {getCsrfToken};
