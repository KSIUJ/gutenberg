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
  interface FetchOptions {
    /**
     * Disable setting `$auth.me` to `Unauthenticated` upon receiving a 401 or 403 response with
     * the appropriate header indicating unauthenticated API access.
     *
     * The name is prefixed with `gutenberg` to avoid breaking changes when updating the `ofetch`
     * package (a dependency of Nuxt 4).
     */
    gutenbergDisableUnauthenticatedHandling?: boolean;
  }
}

export {}
