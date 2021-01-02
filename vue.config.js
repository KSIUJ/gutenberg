/*eslint-disable */
const { CleanWebpackPlugin } = require('clean-webpack-plugin');

module.exports = {
  publicPath: '/static/',
  chainWebpack: (config) => {
    config
      .plugin('html')
      .tap((args) => {
        args[0].template = './webapp/public/index.html';
        return args;
      });
  },
  configureWebpack: {
    resolve: {
      alias: {
        '@': `${__dirname}/webapp/src`,
      },
    },
    entry: {
      app: './webapp/src/main.js',
    },
    plugins: [
      new CleanWebpackPlugin(),
    ],
  },
  transpileDependencies: [
    'vuetify',
  ],
};
