document.addEventListener('DOMContentLoaded', function() {
    if (typeof pdfjsLib === 'undefined') return;
    const url = window.previewUrl || (typeof preview_url !== 'undefined' ? preview_url : null);
    if (!url) return;
    const container = document.getElementById('pdf-preview');
    pdfjsLib.GlobalWorkerOptions.workerSrc = '/static/js/pdfjs/pdf.worker.js';
    pdfjsLib.getDocument(url).promise.then(function(pdf) {
        // Render first 3 pages for preview
        for (let pageNum = 1; pageNum <= Math.min(pdf.numPages, 3); pageNum++) {
            pdf.getPage(pageNum).then(function(page) {
                const viewport = page.getViewport({ scale: 1.2 });
                const canvas = document.createElement('canvas');
                canvas.className = 'mb-3';
                container.appendChild(canvas);
                const context = canvas.getContext('2d');
                canvas.height = viewport.height;
                canvas.width = viewport.width;
                page.render({ canvasContext: context, viewport: viewport });
            });
        }
    });
}); 