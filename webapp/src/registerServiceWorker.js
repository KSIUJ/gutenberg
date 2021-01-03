/* eslint-disable no-console */

import { register } from 'register-service-worker';

if (process.env.NODE_ENV === 'production') {
  register('/service-worker.js', {
    registrationOptions: { scope: '/' },
    ready() {
      console.log(
        'App is being served from cache by a service worker.',
      );
    },
    registered(reg) {
      console.log('Service worker has been registered, scope is:', reg.scope);
    },
    cached() {
      console.log('Content has been cached for offline use.');
    },
    updatefound() {
      console.log('New content is downloading.');
    },
    updated() {
      console.log('New content is available; please refresh.');
    },
    offline() {
      console.log('No internet connection found. App is running in offline mode.');
    },
    error(error) {
      console.error('Error during service worker registration:', error);
    },
  });
}
