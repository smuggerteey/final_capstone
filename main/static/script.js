// script.js

document.addEventListener("DOMContentLoaded", () => {
    const discoverBtn = document.querySelector('a[href="#features"]');

    // Smooth Scroll Effect
    discoverBtn.addEventListener("click", (event) => {
        event.preventDefault();
        document.querySelector('#features').scrollIntoView({
            behavior: 'smooth',
            block: 'start'
        });
    });
});
document.getElementById('registrationForm').addEventListener('submit', function(event) {
    event.preventDefault();

    const password = document.getElementById('password').value;
    const confirmPassword = document.getElementById('confirmPassword').value;

    if (password !== confirmPassword) {
        alert('Passwords do not match!');
        return;
    }

    alert('Account created successfully!');
    window.location.href = "index.html";  // Redirect to landing page after registration
});
