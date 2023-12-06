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
                'md-max': {'max': '1023px'},
                'lg-max': {'max': '1279px'},
                'xl-max': {'max': '1535px'},
            }
        },
    },
    plugins: [
        require("flowbite/plugin")
    ],
}
