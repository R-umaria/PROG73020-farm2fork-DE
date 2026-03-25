async function loadDashboard() {
  const deliveryList = document.getElementById('delivery-list');
  if (!deliveryList) return;

  try {
    const deliveries = await api.getDeliveries();
    deliveryList.innerHTML = '';

    if (!deliveries.length) {
      deliveryList.innerHTML = '<p>No deliveries found.</p>';
      return;
    }

    deliveries.forEach((delivery) => {
      const card = document.createElement('div');
      card.className = 'delivery-card';
      card.innerHTML = `
        <h3>${delivery.order_id}</h3>
        <p>${delivery.customer_name}</p>
        <p>${delivery.address}</p>
        <p><span class="badge">${delivery.status}</span></p>
      `;
      card.addEventListener('click', () => {
        showDeliveryOnMap(delivery);
        renderRouteSummary(delivery);
      });
      deliveryList.appendChild(card);
    });

    // Auto-select the first delivery
    showDeliveryOnMap(deliveries[0]);
    renderRouteSummary(deliveries[0]);
  } catch (error) {
    deliveryList.innerHTML = `<p>Failed to load dashboard data: ${error.message}</p>`;
  }
}

document.addEventListener('DOMContentLoaded', () => {
  if (document.getElementById('map')) {
    initMap();
    loadDashboard();
  }
});
