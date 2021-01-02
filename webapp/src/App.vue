<template>
  <v-app>
    <v-app-bar
      app
      color="secondary"
      dark
      elevation="0"
    >
      <a href="/" class="text-decoration-none white--text">
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
      </a>

      <v-spacer></v-spacer>

      <v-menu offset-y>
        <template v-slot:activator="{ on, attrs }">
          <v-btn class="text-none" plain large :loading="user===null" v-bind="attrs"
                 v-on="on">{{ username }}
            <v-icon>arrow_drop_down</v-icon>
          </v-btn>
        </template>
        <v-list>
          <v-list-item v-if="isStaff" href="/admin/">
            <v-list-item-title>
              Admin Panel
            </v-list-item-title>
          </v-list-item>
          <v-list-item @click="logout">
            <v-list-item-title>Sign out</v-list-item-title>
          </v-list-item>
        </v-list>
      </v-menu>

    </v-app-bar>

    <v-main>
      <v-container style="max-width: 1140px">
        <router-view></router-view>
      </v-container>
    </v-main>
    <form :action="API.logout" method="post" id="logout-form">
      <input type="hidden" name="csrfmiddlewaretoken" :value="getCsrfToken()">
    </form>
    <v-footer padless>
      <v-col
        class="text-center"
        cols="12"
      >
        © 2015 - {{ new Date().getFullYear() }} <a class="text-decoration-none" href="https://ksi.ii.uj.edu.pl/">KSI
        UJ</a> |
        <a class="text-decoration-none" href="https://github.com/KSIUJ/gutenberg">Source</a>
      </v-col>
    </v-footer>
  </v-app>
</template>

<script>

import { API } from './common/api';
import { getCsrfToken } from './common/utils';

export default {
  name: 'App',

  components: {},

  data: () => ({
    API,
    getCsrfToken,
  }),
  watch: {
    $route: {
      handler(to) {
        document.title = `${to.meta.title} | Gutenberg` || 'Gutenberg';
      },
      immediate: true,
    },
  },
  mounted() {
    this.$store.commit('initialiseStore');
    if (this.$store.state.user === null) {
      window.axios.get(API.me).then((value) => {
        this.$store.commit('loginUser', value.data);
      });
    }
  },
  methods: {
    logout() {
      document.getElementById('logout-form').submit();
    },
  },
  computed: {
    username() {
      const { user } = this;
      if (user !== null) {
        return `${user.first_name} ${user.last_name}`;
      }
      return '';
    },
    user: {
      get() {
        return this.$store.state.user;
      },
    },
    isStaff() {
      return this.user && this.user.is_staff;
    },
  },
};
</script>
