document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('certificateForm');
    const preview = document.getElementById('preview');
    const results = document.getElementById('results');
    const errorDiv = document.getElementById('error');
    const loadingDiv = document.createElement('div');
    loadingDiv.className = 'loading';
    loadingDiv.innerHTML = 'Generating certificates...';

    // Preview certificate template when selected
    const templateInput = document.getElementById('template');
    templateInput.addEventListener('change', function() {
        const file = this.files[0];
        if (file) {
            if (!file.type.startsWith('image/')) {
                errorDiv.textContent = 'Please select an image file for the template';
                preview.innerHTML = '';
                return;
            }

            const reader = new FileReader();
            reader.onload = function(e) {
                preview.innerHTML = `
                    <div class="preview-container">
                        <h3>Template Preview:</h3>
                        <img src="${e.target.result}" alt="Template preview" class="preview-image">
                        <div class="preview-overlay">
                            <div class="position-marker" style="left: ${form.x_pos.value}px; top: ${form.y_pos.value}px;">
                                Sample Text
                            </div>
                        </div>
                    </div>`;
                updatePositionMarker();
            };
            reader.readAsDataURL(file);
        }
    });

    // Function to update position marker
    function updatePositionMarker() {
        const marker = document.querySelector('.position-marker');
        if (marker) {
            marker.style.left = `${form.x_pos.value}px`;
            marker.style.top = `${form.y_pos.value}px`;
            marker.style.fontSize = `${form.font_size.value}px`;
            marker.style.color = form.text_color.value;
        }
    }

    // Add listeners for text position inputs
    form.x_pos.addEventListener('input', updatePositionMarker);
    form.y_pos.addEventListener('input', updatePositionMarker);
    form.font_size.addEventListener('input', updatePositionMarker);
    form.text_color.addEventListener('input', updatePositionMarker);

    // Handle form submission
    form.addEventListener('submit', async function(e) {
        e.preventDefault();
        errorDiv.textContent = '';
        results.innerHTML = '';
        
        // Validate inputs
        const template = templateInput.files[0];
        const excel = document.getElementById('excel').files[0];
        
        if (!template || !excel) {
            errorDiv.textContent = 'Please select both template and Excel files';
            return;
        }

        const formData = new FormData(form);
        document.body.appendChild(loadingDiv);

        try {
            const response = await fetch('/generate', {
                method: 'POST',
                body: formData
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.error || 'Failed to generate certificates');
            }

            if (data.success) {
                const resultsHTML = `
                    <div class="results-container">
                        <h3>Certificates Generated Successfully!</h3>
                        <p>Folder: ${data.folder_name}</p>
                        <div class="certificates-list">
                            ${data.certificates.map(cert => `
                                <div class="certificate-item">
                                    <span class="certificate-name">${cert.name}</span>
                                    <a href="${cert.link}" target="_blank" class="certificate-link">
                                        View Certificate
                                    </a>
                                </div>
                            `).join('')}
                        </div>
                    </div>
                `;
                results.innerHTML = resultsHTML;
                results.scrollIntoView({ behavior: 'smooth' });
            }
        } catch (error) {
            errorDiv.textContent = `Error: ${error.message}`;
            console.error('Error occurred:', error);
        } finally {
            loadingDiv.remove();
        }
    });
});