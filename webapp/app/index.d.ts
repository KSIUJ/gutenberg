declare module '#app' {
  // These settings can be used in `definePageMeta`
  // See https://nuxt.com/docs/4.x/guide/directory-structure/app/pages#typing-custom-metadata
  interface PageMeta {
    /**
     * Hide the sign-in button from the header,
     * used for the sign-in page.
     */
    hideSignInButton?: boolean;
  }
}

declare module 'ofetch' {
  // The names are prefixed with `gutenberg` to avoid breaking changes when updating the `ofetch`
  // package (a dependency of Nuxt 4).
  interface FetchOptions {
    /**
     * Add the `Accept` header with the value `application/json` to the request.
     * Verify that the response contains the `Content-Type` header with the value `application/json`.
     */
    gutenbergExpectJson?: boolean;

    /**
     * Disable setting `$auth.me` to `Unauthenticated` upon receiving a 401 or 403 response with
     * the appropriate header indicating unauthenticated API access.
     */
    gutenbergDisableUnauthenticatedHandling?: boolean;
  }
}

export {};
