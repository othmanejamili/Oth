document.addEventListener("DOMContentLoaded", function() {
    document.querySelectorAll(".delete-btn").forEach(button => {
        button.addEventListener("click", function() {
            let productId = this.getAttribute("data-id");
            let row = document.getElementById("product-"+productId);

            if(confirm("Are you sure do you want delete this product")){
                fetch(`/product/delete/${productId}/`, {  
                    method:"POST",
                    headers:{
                        "X-CSRFToken":csrfToken,
                        "content-type":"application/json"
                    },
                    body: JSON.stringify({})  
                })
                .then(response=>response.json())
                .then(data => {
                    if(data.success){
                        row.style.transition = "opacity 0.5s";
                        row.style.opacity = 0;
                        setTimeout(() => row.remove(), 500);
                    }else{
                        return alert("Error: there's problem handling object");
                    }
                })
                .catch(error => {
                    console.log("there is problem of dalate the product",error);
                    return alert("there is problem of dalate the product");
                });
            }
        });
    });
});