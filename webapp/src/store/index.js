import Vue from 'vue';
import Vuex from 'vuex';

Vue.use(Vuex);

function parseBool(val) {
  return val === 'true';
}

function loadFromStore(state, property, conv_fn = (val) => (val)) {
  const val = localStorage.getItem(property);
  if (val) {
    state[property] = conv_fn(val);
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
    fitToPage: null,
    files: [],
  },
  mutations: {
    loginUser(state, user) {
      state.user = user;
    },
    initialiseStore(state) {
      loadFromStore(state, 'colorPrinting', parseBool);
      loadFromStore(state, 'printerId', parseInt);
      loadFromStore(state, 'twoSided');
      loadFromStore(state, 'fitToPage', parseBool);
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
    updateFitToPage(state, value) {
      saveToStore(state, 'fitToPage', value);
    },
    setFiles(state, files) {
      state.files = files;
    },
  },
  actions: {},
  modules: {},
});
