document.getElementById('addProductForm').addEventListener("submit", function(event) {
    event.preventDefault();

    let form = document.getElementById("addProductForm");
    let addProductUrl = form.getAttribute("data-url");
    let formData = new FormData(form);
    let messageDiv = document.getElementById('message');
    let submitButton = form.querySelector("button[type='submit']");
    let spinner = document.getElementById("spinner");
    let csrfToken = document.querySelector("[name=csrfmiddlewaretoken]").value;

    // Clear previous messages
    messageDiv.innerHTML = "";
    messageDiv.classList.remove("show");

    // Disable button and show spinner
    submitButton.disabled = true;
    spinner.style.display = "inline-block";
    submitButton.innerHTML = "Adding...";

    // Price validation
    let price = parseFloat(formData.get("price"));
    if (isNaN(price) || price <= 0) {
        showMessage('error', 'The price should be greater than 0');
        resetButton();
        return;
    }

    // Image validation
    let images = formData.getAll("images");
    if (images.length === 0) {
        showMessage('error', 'At least one image is required');
        resetButton();
        return;
    }

    // Send request to the server
    fetch(addProductUrl, {
        method: "POST",
        body: formData,
        headers: {
            'X-CSRFToken': csrfToken
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            showMessage('error', data.error);
        } else {
            showMessage('success', data.message);
            form.reset(); // Reset form on success
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showMessage('error', 'Something went wrong. Please try again.');
    })
    .finally(() => resetButton());

    // Helper functions
    function showMessage(type, message) {
        messageDiv.innerHTML = `<p class='${type}'>${message}</p>`;
        messageDiv.classList.add("show");
    }

    function resetButton() {
        submitButton.disabled = false;
        spinner.style.display = "none";
        submitButton.innerHTML = "Add Product";
    }
});