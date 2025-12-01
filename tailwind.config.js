// tailwind.config.js
module.exports = {
    content: [
        "./templates/**/*.html",
        "./static/**/*.js",
    ],
    theme: {
        extend: {
            screens: {
                nav: "1400px", 
            },
        },
    },
    plugins: [],
};
