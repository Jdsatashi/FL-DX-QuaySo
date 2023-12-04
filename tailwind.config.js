/** @type {import('tailwindcss').Config} */
module.exports = {
    content: [
        './src/**/*.html',
        './src/static/scripts/**/*.js',
        './src/static/styles/**/*.css',
        "./node_modules/flowbite/**/*.js"
    ],
    theme: {
        extend: {
            screens: {
                'sm-max': {'max': '767px'},
            }
        },
    },
    plugins: [
        require("flowbite/plugin")
    ],
}
