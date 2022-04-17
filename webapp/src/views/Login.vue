<template>
  <div>
    <h1 class="text-h2 mb-10 mt-4">Login</h1>

    <v-alert :value="errorMessage.length > 0" type="error" class="my-5"
             transition="fade-transition">
      {{ errorMessage }}
    </v-alert>

    <v-form ref="form" v-model="form_valid" @submit="submitLogin" v-on:submit.prevent>
      <v-text-field outlined label="Username" type="text" required prepend-icon="person"
                    name="username" :rules="loginRules" v-model="username">
      </v-text-field>
      <v-text-field outlined label="Password" type="password" required prepend-icon="key"
                    name="password" :rules="passwordRules" v-model="password">
      </v-text-field>

      <div class="d-flex justify-end">
        <v-btn class="mt-1 mb-5" large color="primary" :disabled="!form_valid"
               :loading="!token_loaded" type="submit">Submit
        </v-btn>
      </div>

    </v-form>
  </div>
</template>

<script>
// @ is an alias to /src

import { API } from '@/common/api';
import { getCsrfToken } from '../common/utils';

export default {
  name: 'Login',
  data() {
    return {
      form_valid: false,
      token_loaded: false,
      username: null,
      password: null,
      errorMessage: '',
      getCsrfToken,
      loginRules: [
        (v) => !!v || 'Username is required',
      ],
      passwordRules: [
        (v) => !!v || 'Password is required',
      ],
    };
  },
  mounted() {
    window.axios.get(API.login).then(() => {
      this.token_loaded = true;
    });
  },
  methods: {
    submitLogin() {
      window.axios.post(API.login, {
        username: this.username,
        password: this.password,
      }, { noIntercept: true }).catch((err) => {
        this.errorMessage = err.response.data.message;
      }).then((resp) => {
        if (resp && resp.status === 200) {
          this.$emit('login');
          this.$router.push({
            name: 'Print',
          });
        }
      });
    },
  },
  computed: {},
  components: {},
};
</script>
