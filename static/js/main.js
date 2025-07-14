document.addEventListener('DOMContentLoaded', function() {
    const cards = document.querySelectorAll('.operation-card');
    const uploadForm = document.getElementById('uploadForm');
    const selectedOperation = document.getElementById('selectedOperation');
    const deletePagesInput = document.getElementById('deletePagesInput');
    const splitRangesInput = document.getElementById('splitRangesInput');
    const watermarkTextInput = document.getElementById('watermarkTextInput');

    function hideAllExtraInputs() {
        deletePagesInput.classList.add('d-none');
        splitRangesInput.classList.add('d-none');
        watermarkTextInput.classList.add('d-none');
    }

    cards.forEach(card => {
        card.addEventListener('click', function() {
            cards.forEach(c => c.classList.remove('border-primary', 'shadow-lg'));
            this.classList.add('border-primary', 'shadow-lg');
            selectedOperation.value = this.getAttribute('data-operation');
            uploadForm.classList.remove('d-none');
            uploadForm.classList.add('animate__animated', 'animate__fadeInUp');
            uploadForm.scrollIntoView({ behavior: 'smooth' });
            hideAllExtraInputs();
            if (this.getAttribute('data-operation') === 'delete') {
                deletePagesInput.classList.remove('d-none');
            } else if (this.getAttribute('data-operation') === 'split') {
                splitRangesInput.classList.remove('d-none');
            } else if (this.getAttribute('data-operation') === 'watermark') {
                watermarkTextInput.classList.remove('d-none');
            }
        });
    });
}); 