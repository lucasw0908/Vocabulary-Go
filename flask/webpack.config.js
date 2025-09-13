const path = require('path');

module.exports = {
  entry: {
    main: './app/static/assets/js/main.js',
    word_test: './app/static/assets/js/word_test.js',
    sentence_test: './app/static/assets/js/sentence_test.js',
    library: './app/static/assets/js/library.js',
    library_edit: './app/static/assets/js/library_edit.js',
    library_edit_select: './app/static/assets/js/library_edit_select.js',
    library_create: './app/static/assets/js/library_create.js',
    card: './app/static/assets/js/card.js',
    'bg-anime': './app/static/assets/js/bg-anime.js'
  },
  output: {
    filename: '[name].bundle.js',
    path: path.resolve(__dirname, './app/static/assets/js/dist')
  }
};
