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
     * Raise an error if the response is empty (HTTP status 204).
     */
    gutenbergRequireNonEmpty?: boolean;

    /**
     * Disable setting `$auth.me` to `Unauthenticated` upon receiving a 401 or 403 response with
     * the appropriate header indicating unauthenticated API access.
     */
    gutenbergDisableUnauthenticatedHandling?: boolean;
  }
}

export {};
