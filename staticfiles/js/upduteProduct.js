document.getElementById('updateProductForm').addEventListener("submit", function(event) {
    event.preventDefault();

    let form = document.getElementById('updateProductForm');
    let formData = new FormData(form);
    let messageDiv = document.getElementById('message');  // Corrected ID
    let submitButton = document.querySelector("button[type='submit']");
    let spinner = document.getElementById('spinner');
    let csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;

    messageDiv.innerHTML = "";
    messageDiv.classList.remove("show", "error", "success"); // Reset classes

    submitButton.disabled = true;
    spinner.style.display = "inline-block";
    submitButton.textContent = "Updating...";

    // Get the product ID from the form's action URL
    let productId = "{{ product.id }}";

    let price = parseFloat(formData.get("price"));
    if (isNaN(price) || price <= 0) {
        showMessage('error', 'The price should be greater than 0');
        resetButton();
        return;
    }

    let images = form.querySelector("input[name='images']").files;
    if (images.length === 0) {
        showMessage('error', 'You should upload at least one picture');
        resetButton();
        return;
    }

    fetch(`/product/update/${productId}/`, {
        method: 'POST',
        body: formData,
        headers: {
            "X-CSRFToken": csrfToken
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            showMessage('error', data.error);
        } else {
            showMessage('success', data.message);
            form.reset();
        }
    })
    .catch(error => {
        console.log('Error:', error);
        showMessage('error', 'Something went wrong. Please try again.');
    })
    .finally(() => resetButton());

    function showMessage(type, message) {
        messageDiv.innerHTML = `<p class="${type}">${message}</p>`;
        messageDiv.classList.add("show");
    }

    function resetButton() {
        submitButton.disabled = false;
        spinner.style.display = "none";
        submitButton.textContent = "Update Product";
    }
});
