// addProduct.js
document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('addProductForm');
    const messageContainer = document.getElementById('message');
    const submitButton = document.getElementById('submitBtn');
    const spinner = document.getElementById('spinner');
    const imageInput = document.getElementById('images');
    const previewContainer = document.getElementById('preview');
    
    // Image preview functionality × - ` message-container inlone block
    imageInput.addEventListener('change', function() {
        previewContainer.innerHTML = '';

        if (this.files) {
            Array.from(this.files).forEach((file, index) => {
                if (!file.type.match('image.*')) {
                    return;
                }

                const reader = new FileReader();

                reader.onload = function(e) {
                    const perviewItem = document.createElement('div');
                    perviewItem.className = "preview-item";
                    perviewItem.innerHTML = `
                        <img src=${e.target.result} alt="perview image" >
                        <button type="button" class="preview-remove" data-index=${index}>×</button>
                    `;
                    previewContainer.appendChild(perviewItem);

                    perviewItem.querySelector(".preview-remove").addEventListener('click', function() {
                        perviewItem.remove();
                    });
                };
                reader.readAsDataURL(file);
            });
        }
    });

    form.addEventListener('submit', function(event) {
        event.preventDefault();
        
        if (!ValidateForm) {
            return;
        }

        const formData = new FormData(form);

        setLoadingState(true)

        fetch(form.action , {
            method:'POST',
            body: formData,
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            }
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`server Reponde With ${response.status}: ${response.statusText}`);
            }
            return response.json();
        })
        .then(data => {
            if (data.error) {
                showMessage('error', data.error)
            } else {
                showMessage('success', data.message || 'Add Product Successfully');
                form.reset();
                previewContainer.innerHTML = '';
            }
        })
        .catch(error => {
            console.error('Error',error);
            showMessage('error','An error occurred while submitting the form. Please try again.');
        })
        .finally(()=>  {
            setLoadingState(false)
        })

    })

    function ValidateForm() {
        clearMessage();

        const price = parseFloat(form.price.value);
        if (isNaN(price) || price <= 0) {
            showMessage('error','Please enter a valid price greater than zero.');
            form.price.focus();
            return false;
        }

        if (imageInput.files.length === 0) {
            showMessage('error','Please select at least one image for the product.');
            return false;
        }

        const totalSize = 0;
        const maxSixe = 10 * 1024 * 1024;
        for (let i = 0; i < imageInput.files.length; i++) {
            const file = imageInput.files[i];
            
            if (!file.type.match('image.*')) {
                showMessage('error','Please select only image files.');
                return false;
            }

            totalSize += file.size;
        }
        if (totalSize < maxSixe) {
            showMessage('error','Total image size exceeds the 10MB limit.');
            return false;
        }
        return true;
    }

    function showMessage(type, text) {
        messageContainer.innerHTML = `<p class="message-text">${text}</p>`;
        messageContainer.className=`message-container ${type} show`;

        messageContainer.scrollIntoView({behavior:'smooth' , block:'nearest'});
    };

    function clearMessage() {
        messageContainer.innerHTML='';
        messageContainer.className= 'message-container';
    };

    function setLoadingState(isLoading) {
        if (isLoading) {
            submitButton.disable = true;
            spinner.style.display = 'inline-block';
            submitButton.querySelector('span').textContent = 'Processing...';
        } else {
            submitButton.disable = false;
            spinner.style.display = 'none';
            submitButton.querySelector('span').textContent = 'Add Product';
        }
    };

});