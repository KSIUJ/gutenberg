const { CleanWebpackPlugin } = require('clean-webpack-plugin');
const CompressionPlugin = require('compression-webpack-plugin');

module.exports = {
  publicPath: '/static/',
  chainWebpack: (config) => {
    config
      .plugin('html')
      .tap((args) => {
        // eslint-disable-next-line no-param-reassign
        args[0].template = './webapp/public/index.html';
        return args;
      });
    config.plugins.delete('prefetch');
    config.plugin('CompressionPlugin').use(CompressionPlugin);
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
  pwa: {
    name: 'Gutenberg',
    themeColor: '#343a40',
    msTileColor: '#343a40',
    appleMobileWebAppCapable: 'yes',
    appleMobileWebAppStatusBarStyle: 'black',
    manifestOptions: {
      start_url: '/',
      scope: '/',
      icons: [
        {
          src: '/static/img/icons/android-launchericon-96-96.png',
          sizes: '96x96',
          type: 'image/png',
          purpose: 'any maskable',
        },
        {
          src: '/static/img/icons/android-launchericon-144-144.png',
          sizes: '144x144',
          type: 'image/png',
          purpose: 'any maskable',
        },
        {
          src: '/static/img/icons/android-launchericon-192-192.png',
          sizes: '192x192',
          type: 'image/png',
          purpose: 'any maskable',
        },
        {
          src: '/static/img/icons/android-launchericon-512-512.png',
          sizes: '512x512',
          type: 'image/png',
          purpose: 'any maskable',
        },
      ],
    },
    iconPaths: {
      favicon32: 'img/icons/favicon-32x32.png',
      favicon16: 'img/icons/favicon-16x16.png',
      appleTouchIcon: 'img/icons/apple-touch-icon.png',
      maskIcon: 'img/icons/safari-pinned-tab.svg',
      msTileImage: 'img/icons/mstile-150x150.png',
    },

    // configure the workbox plugin
    workboxPluginMode: 'GenerateSW',
    workboxOptions: {
      exclude: [
        /^.*html(\..*)?$/,
        /^.*map(\..*)?$/,
        /^.*json(\..*)?$/,
        /^$/,
      ],
      clientsClaim: true,
    },
  },
};
