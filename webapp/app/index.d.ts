// See https://nuxt.com/docs/4.x/guide/directory-structure/app/pages#typing-custom-metadata

declare module '#app' {
  // These settings can be used in `definePageMeta`
  interface PageMeta {
    /**
     * Hide the sign-in button from the header,
     * used for the sign-in page.
     */
    hideSignInButton?: boolean;
  }
}

export {}
