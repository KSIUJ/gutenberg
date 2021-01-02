<template>
  <v-app>
    <v-app-bar
      app
      color="secondary"
      dark
      elevation="0"
    >
      <div class="d-flex align-center">
        <v-img
          alt="Gutenberg logo"
          class="shrink mr-2 ml-3"
          contain
          src="./assets/logo-120.png"
          transition="scale-transition"
          width="40"
        />
        <v-toolbar-title>Gutenberg</v-toolbar-title>
      </div>

      <v-spacer></v-spacer>

    </v-app-bar>

    <v-main>
      <v-container style="max-width: 1140px">
        <router-view></router-view>
      </v-container>
    </v-main>
  </v-app>
</template>

<script>

export default {
  name: 'App',

  components: {},

  data: () => ({
    //
  }),
  watch: {
    $route: {
      handler(to) {
        document.title = `${to.meta.title} | Gutenberg` || 'Gutenberg';
      },
      immediate: true,
    },
  },
};
</script>
