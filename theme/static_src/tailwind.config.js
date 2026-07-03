module.exports = {
  content: [
    "../../templates/**/*.html",
    "../../**/templates/**/*.html",
    "../../**/*.html"
  ],
  theme: {
    extend: {},
  },
  plugins: [
    require("daisyui"),
  ],
}