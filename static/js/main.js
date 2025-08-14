// Modal open/close logic
window.addEventListener('DOMContentLoaded', function() {
    var modal = document.getElementById('dateModal');
    var openBtn = document.getElementById('openModalBtn');
    var closeBtn = document.getElementById('closeModalBtn');
    openBtn.onclick = function() {
        modal.style.display = 'block';
    }
    closeBtn.onclick = function() {
        modal.style.display = 'none';
    }
    window.onclick = function(event) {
        if (event.target == modal) {
            modal.style.display = 'none';
        }
    }
});
