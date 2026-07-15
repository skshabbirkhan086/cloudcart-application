const api = "/api";

async function loadProducts() {
  const products = await fetch(`${api}/products`).then(r => r.json());
  document.getElementById("products").innerHTML = products.map(p =>
    `<article><h3>${p.name}</h3><p>₹${p.price}</p><p>Stock: ${p.stock}</p></article>`
  ).join("");
  document.getElementById("product").innerHTML = products.map(p =>
    `<option value="${p.id}">${p.name}</option>`
  ).join("");
}

async function loadOrders() {
  const orders = await fetch(`${api}/orders`).then(r => r.json());
  document.getElementById("orders").innerHTML = orders.map(o =>
    `<tr><td>${o.id}</td><td>${o.customer_name}</td><td>${o.status}</td><td>₹${o.total_amount}</td></tr>`
  ).join("");
}

document.getElementById("order-form").addEventListener("submit", async event => {
  event.preventDefault();
  const response = await fetch(`${api}/orders`, {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify({
      customer_name: document.getElementById("customer").value,
      product_id: Number(document.getElementById("product").value),
      quantity: Number(document.getElementById("quantity").value)
    })
  });
  const body = await response.json();
  document.getElementById("message").textContent =
    response.ok ? `Created ${body.id}` : body.detail;
  await loadProducts();
  await loadOrders();
});

loadProducts();
loadOrders();
setInterval(loadOrders, 5000);
