import Vue from 'vue';
import Vuex from 'vuex';

Vue.use(Vuex);

export default new Vuex.Store({
  strict: true,
  state: {
    user: null
  },
  mutations: {
    loginUser(state, user) {
      state.user = user
    },
    initialiseStore(state) {
    }
  },
  actions: {},
  modules: {},
});
