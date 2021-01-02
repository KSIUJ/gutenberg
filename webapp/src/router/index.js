import Vue from 'vue';
import VueRouter from 'vue-router';
import Print from '../views/Print.vue';
import JobStatus from '../views/JobStatus.vue';

Vue.use(VueRouter);

const routes = [
  {
    path: '/',
    name: 'Print',
    component: Print,
    meta: {
      title: 'Print',
    },
  },
  {
    path: '/job/:id/',
    name: 'JobStatus',
    component: JobStatus,
    pathToRegexpOptions: { strict: true },
    meta: {
      title: 'Job status',
    },
  },
];

const router = new VueRouter({
  mode: 'history',
  base: '/', // process.env.BASE_URL,
  routes,
});

export default router;
