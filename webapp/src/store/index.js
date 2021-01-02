import Vue from 'vue';
import Vuex from 'vuex';

Vue.use(Vuex);

function loadFromStore(state, property) {
  const val = localStorage.getItem(property);
  if (val) {
    state[property] = val;
  }
}

function saveToStore(state, property, value) {
  state[property] = value;
  localStorage.setItem(property, value);
}

export default new Vuex.Store({
  strict: true,
  state: {
    user: null,
    colorPrinting: null,
    printerId: null,
    twoSided: null,
  },
  mutations: {
    loginUser(state, user) {
      state.user = user;
    },
    initialiseStore(state) {
      loadFromStore(state, 'colorPrinting');
      loadFromStore(state, 'printerId');
    },
    updateColorPrinting(state, value) {
      saveToStore(state, 'colorPrinting', value);
    },
    updatePrinterId(state, value) {
      saveToStore(state, 'printerId', value);
    },
    updateTwoSided(state, value) {
      saveToStore(state, 'twoSided', value);
    },
  },
  actions: {},
  modules: {},
});
