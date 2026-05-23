document.addEventListener('DOMContentLoaded', function () {
    const selects = document.querySelectorAll('select');
    selects.forEach(select => {
        select.addEventListener('change', function () {
            this.classList.add('active-select');
        });
    });
});
