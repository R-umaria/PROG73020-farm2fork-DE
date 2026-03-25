function renderRouteSummary(delivery) {
  const routeSummary = document.getElementById('route-summary');
  if (!routeSummary) return;

  routeSummary.innerHTML = `
    <div class="delivery-card">
      <h3>Order ${delivery.order_id}</h3>
      <p><strong>Customer:</strong> ${delivery.customer_name}</p>
      <p><strong>Address:</strong> ${delivery.address}</p>
      <p><strong>Status:</strong> <span class="badge">${delivery.status}</span></p>
      <p><strong>Map provider:</strong> OpenStreetMap</p>
      <p><strong>Renderer:</strong> Leaflet</p>
      <p><strong>Next step:</strong> Replace demo line rendering with a true routing engine API when your team is ready.</p>
      <a class="button" href="/delivery/${delivery.id}">Open Delivery Detail</a>
    </div>
  `;
}
