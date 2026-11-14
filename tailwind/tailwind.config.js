/** Busca clases en plantillas, JS y Python (widgets de formularios). Rutas relativas a la raíz del proyecto. */
module.exports = {
  content: [
    "./templates/**/*.html",
    "./*/templates/**/*.html",
    "./*/static/**/*.js",
    "./*/*.py",
    "./*/templatetags/*.py",
  ],
  theme: { extend: {} },
  plugins: [],
};
