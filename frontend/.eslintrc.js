module.exports = {
  root: true,
  env: {
    node: true,
  },
  extends: ["plugin:vue/essential", "@vue/prettier"],
  rules: {
    "vue/multi-word-component-names": "off",
    "vue/no-v-for-template-key": "off",
  },
  parserOptions: {
    ecmaVersion: 2020,
  },
};
