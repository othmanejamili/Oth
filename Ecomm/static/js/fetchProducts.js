document.addEventListener("DOMContentLoaded", function () {
    const PAGE_SIZE = 5; // Number of items per page
    let currentPage = 1;
    let currentSort = { field: null, ascending: true };
    let productsData = []; // Store the fetched data

    // Initial fetch
    fetchProducts();

    // Add sort handlers to table headers
    document.querySelectorAll("#product-table th[data-sort]").forEach(header => {
        header.addEventListener('click',() =>{
            if (currentSort.field === field) {
                currentSort.ascending = !currentSort.ascending
            } else {
                currentSort.ascending = true
            }
        });
        displayProducts();
        updateSortIndicators();
    });

    // Pagination controls
    document.getElementById('prvPage').addEventListener('click', ()=>{
        if (currentPage > 1) {
            currentPage--;
            displayProducts();
        }
    });

    document.getElementById('nextPage').addEventListener('click', ()=>{
        let maxpage = math.ceil(productsData.length / PAGE_SIZE)
        if (currentPage > maxpage) {
            currentPage++;
            displayProducts();
        }
    });

    function showLoading() {
        const productTable = document.querySelector("#product-table tbody");
        productTable.innerHTML = `
            <tr>
                <td colspan="5" class="text-center">
                    <div class="spinner-border text-primary" role="status">
                        <span class="visually-hidden">Loading...</span>
                    </div>
                    <p class="mt-2">Loading products...</p>
                </td>
            </tr>
        `;
    }

    function showError(error, retryFn) {
        const productTable = document.querySelector("#product-table tbody");
        productTable.innerHTML = `
            <tr>
                <td colspan="5" class="text-center">
                    <div class="alert alert-danger" role="alert">
                        Error loading products: ${error}
                        <button class="btn btn-danger btn-sm ms-3" onclick="retryFetch()">
                            Retry
                        </button>
                    </div>
                </td>
            </tr>
        `;
        window.retryFetch = retryFn;
    }

    async function fetchProducts() {
        showLoading();
        
        try{
            let response = await fetch('/get-products/', {
                headers:{
                    'X-Requested-With':'XMLHttpRequest',
                    'X-CSRFToken':csrfToken
                }
            });

            if (response.ok) {
                throw new Error(`we have error: ${response.status}`)
            };

            const data = await response.json();
            productsData = data.Products;

            displayProducts();

            updatePagination();

        } catch(error){
            console.log('error tha fucking shit:',error)
            showError(error.message,fetchProducts)
        } 
    }

    function displayProducts() {
        const productTable = document.querySelector("#product-table tbody");
        productTable.innerHTML ="";

        if (productTable.length===0) {
            productTable.innerHTML = `<tr><td colspan="5" class="text-center">No products available.</td></tr>`;
            return;
        }

        // Sort data if needed
        let displayData = [...productsData];
        if (currentSort.field) {
            displayData.sort((a, b) => {
                let comparison = 0;
                if (a[currentSort.field] < b[currentSort.field]) comparison = -1;
                if (a[currentSort.field] > b[currentSort.field]) comparison = 1;
                return currentSort.ascending ? comparison : -comparison;
            });
        }

        // Paginate data
        const start = (currentPage - 1) * PAGE_SIZE;
        const paginatedData = displayData.slice(start, start + PAGE_SIZE);

        // Display data
        paginatedData.forEach(product => {
            const imageHTML = product.images.length > 0
                ? product.images.map(img => `<img src="${img}" alt="${product.name}" class="product-image">`).join(" ")
                : "No Image Available";

            const row = `
                <tr>
                    <td>${escapeHTML(product.name)}</td>
                    <td>${escapeHTML(product.description)}</td>
                    <td>$${Number(product.price).toFixed(2)}</td>
                    <td>${escapeHTML(product.size)}</td>
                    <td>${imageHTML}</td>
                </tr>
            `;
            productTable.innerHTML += row;
        });
    }

    function updatePagination() {
        const totalPages = Math.ceil(productsData.length / PAGE_SIZE);
        document.getElementById('currentPage').textContent = `Page ${currentPage} of ${totalPages}`;
        document.getElementById('prevPage').disabled = currentPage === 1;
        document.getElementById('nextPage').disabled = currentPage === totalPages;
    }

    function updateSortIndicators() {
        document.querySelectorAll('#product-table th[data-sort]').forEach(header => {
            const field = header.dataset.sort;
            const indicator = header.querySelector('.sort-indicator');
            if (field === currentSort.field) {
                indicator.textContent = currentSort.ascending ? '↑' : '↓';
                indicator.classList.remove('d-none');
            } else {
                indicator.classList.add('d-none');
            }
        });
    }

    function escapeHTML(str) {
        const div = document.createElement('div');
        div.textContent = str;
        return div.innerHTML;
    }
});